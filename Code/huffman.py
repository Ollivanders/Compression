import heapq as heap
import os.path
import time
from bitarray import bitarray
from operator import itemgetter

""" A class for the nodes of the huffman tree.
Each node has a character value, a frequency (the number of times it appears in the file),
 and a left and right child. Each of the children are nodes of themselves or are equal to 'None' """


class Node:
    def __init__(self, value, frequency):
        self.left = None
        self.right = None
        self.value = value
        self.frequency = frequency

    # set children of the current node
    def set_children(self, l, r):
        self.left = l
        self.right = r

    # a comparative function that compares the frequency of the node with another, used when creating the heap
    def __lt__(self, other):
        return self.frequency < other.frequency


""" A function that recursively calls itself. It creates a list of tuples 'code_lengths',
which details the character value and the length of the huffman code for that character was it to be created.
For this version, codebook creation is canonical so computation time is saved by not calculating the code.
The resulting codebook is generated and returned as a dictionary"""


def write_code_lengths(current_node, codeword_size, code_lengths):
    if current_node.value:  # if a leaf, the node.value is none
        if not codeword_size:
            code_lengths[current_node.value] = 0
        else:
            code_lengths[current_node.value] = codeword_size
    # expands out and calls the function for the nodes children
    else:
        write_code_lengths(current_node.left, codeword_size + 1, code_lengths)  # calls the function again
        write_code_lengths(current_node.right, codeword_size + 1, code_lengths)


""" Generates a canonical code from a list of tuples (character, length),
ordered by code length and then alphabetically, 
returns a code_book as a list of tuples (char, binary_code) that is sorted character value"""


def write_codebook(ordered_code_lengths):
    codebook = []
    current_length = ordered_code_lengths[0][1]  # sets the inital start length
    code_int = 0

    for i in ordered_code_lengths:
        # bit shifts the number of times that the current length differs from the previous
        code_int = code_int << (i[1] - current_length)
        current_length = i[1]  # resets the length
        # converts the integer value to binary with the correct bit length
        code = format(code_int, "0" + str(current_length) + "b")
        codebook.append((i[0], code))  # adds the new code to the list
        code_int += + 1

    codebook.sort()  # sorts the codebook list into by the first value, alphabetically
    return codebook


def codebook_output_canonical(codebook_list):
    codebook_output = ""
    previous_val = 0
    for val in codebook_list:
        for i in range(previous_val, val[0] - 1):
            codebook_output += "0"  # adds zeros' if a length for the character is not available
        previous_val = val[0]
        codebook_output += "1"  # adds a zero if length is available, length presented next
        codebook_output += format(len(val[1]), "06b")  # converts the length to binary
    for n in range(previous_val, 256):
        codebook_output += "0"
    return codebook_output


def codebook_output_tradition(codebook_list):
    codebook_output = ""
    for x in codebook_list:
        codebook_output += format(x[0], "08b")
        codebook_output += format(len(x[1]), "04b")
    return codebook_output


"""Compresses a file into a smaller version with the extension '.hc' from the InputFiles/ directory"""


def encode(file_name):  # compress the file
    file = open("InputFiles/" + file_name, "r")  # opens the file from the InputFiles directory
    input_size = os.path.getsize("InputFiles/" + file_name)  # finds the input size for later comparison
    data = file.read()  # assigns the data as a bytes variable

    frequencies = {}  # dictionary of each character and its relative frequency
    for x in data:
        if x in frequencies.keys():  # if the character x is already a key
            frequencies[x] += 1
        else:  # therefore x is not a key yet
            frequencies[x] = 1

    node_list = []
    # creates a list of all nodes for each character
    for val, freq in frequencies.items():
        added_node = Node(val, freq)
        node_list.append(added_node)

    # The heap stores everything in reverse order to start, collects up nodes, adding them back on to the heap
    # uses the heap module to do this efficiently
    heap.heapify(node_list)

    while len(node_list) > 1:  # while the heap still has a root
        right = heap.heappop(node_list)  # heappop returns the smallest value
        left = heap.heappop(node_list)
        new_node = Node(None, right.frequency + left.frequency)  # therefore only the leaves have a data value
        new_node.set_children(left, right)
        heap.heappush(node_list, new_node)  # updates the heap
    root = node_list[0]  # now node_list contains only the root with all other nodes stretching from it

    code_lengths = {}  # dictionary of the code lengths for each character
    write_code_lengths(root, 0, code_lengths)
    ordered_code_lengths = sorted(code_lengths.items(), key=itemgetter(1, 0))
    codebook_list = write_codebook(ordered_code_lengths)  # converts the code_lengths to canonical code
    codebook_dict = {}  # creates the codebook as a dictionary to use the bitarray encode function
    for i in codebook_list:
        codebook_dict[i[0]] = bitarray(i[1])

    output_file = open("CompressedFiles/" + file_name.split(".")[0] + ".hc", "wb")
    codebook_output = ""

    # writes the code lengths to the start of the file, starts as a string
    output_can = codebook_output_canonical(codebook_list)
    output_trad = codebook_output_tradition(codebook_list)
    if len(output_can) > len(output_trad):
        codebook_output = "0" + format(len(output_trad), "011b") + output_trad
    else:
        codebook_output = "1" + output_can
    book_list = bitarray(codebook_output)  # converts to bitarray
    book_add = book_list.buffer_info()[3]
    book_add_binary = format(book_add, "08b")  # add is short for additional
    book_list = bitarray(bitarray(book_add_binary + "0" * book_add) + book_list)  # adds zeros to ensure multiple of 8
    book_list.tofile(output_file)  # writes the codebook to the file

    text_list = bitarray(endian="little")
    text_list.encode(codebook_dict, data)  # text list is a bitarray of the text encoded
    text_add = text_list.buffer_info()[3]  # finds the number of unused bits to match it up to 8
    text_add_binary = format(text_add, "08b")  # appends this number of 0's
    text_list = bitarray(bitarray(text_add_binary + "0" * text_add) + text_list)  # ensures multiple of 8
    text_list.tofile(output_file)
    output_file.close()

    output_size = os.path.getsize("CompressedFiles/" + file_name.split(".")[0] + ".hc")  # size of output file

    if (output_size > input_size):
        output_file.close()
        print("Your file cannot be compressed any further so has been left as a txt file")

    print("\nOutput Size: " + str(output_size))
    print("Input Size: " + str(input_size))
    print("------------> Compression Ratio: " + str((1 - (output_size / input_size)) * 100) + "%")


"""Decompresses a file with the extension '.hc' into a '.txt' file from the CompressedFiles/ directory"""


def decode(file_name):
    file = open("CompressedFiles/" + file_name.split(".")[0] + ".hc", "rb")  # reads the file in binary
    data = file.read()
    # converts the bytes to bits in 8 bit form, allocating it to one long string
    code = ""
    for i in data:
        code += format(i, "08b")

    # extracts the codebook
    book_buffer = int(code[0:8], 2) + 8  # number of added bits and the number
    code = code[book_buffer:]  # taken off the start

    binary_lengths = []
    ordered_codelengths = []
    book_format = code[0]
    code = code[1:]
    if book_format == "1":
        for i in range(0, 256):  # i tracks what character we are on
            bit = code[0]
            code = code[1:]  # skips of 0's
            if bit == "1":  # 1 means the next 6 digits are the length of a codeword
                binary_lengths.append(code[0:6])  # length added to the binary lengths string
                code = code[6:]
            else:
                binary_lengths.append("0")  # zero showed it no length given

        # converts the lengths in binary to int values
        lengths = []
        for x in binary_lengths:
            lengths.append(int(x, 2))

        # gets rid of the 0's and makes a list of tuples with the character and the codeword length
        for i in range(0, 255):  # 255 because of list indexing
            if lengths[i] != 0:
                ordered_codelengths.append((i + 1, lengths[i]))
    else:
        codebook_length = int(code[:11], 2) + 11
        codebook_string = code[11:codebook_length]
        code = code[codebook_length:]
        while 0 < len(codebook_string):
            ordered_codelengths.append((int(codebook_string[:8], 2), int(codebook_string[8:12], 2)))
            codebook_string = codebook_string[12:]

    # engineers the codebook from the ordered_codelengths as performed in encoding
    codebook_list = write_codebook(sorted(ordered_codelengths, key=itemgetter(1, 0)))
    codebook_dict = {}
    for i in codebook_list:
        codebook_dict[chr(i[0])] = bitarray(i[1])

    text_buffer = int(code[0:8], 2) + 8  # gets rid of the buffer created when the text is added
    code = code[text_buffer:]
    output_file = open("DecompressedFiles/" + file_name.split(".")[0] + ".txt", "w")
    text = bitarray(code)
    output_file.write(
        ''.join(text.decode(codebook_dict)))  # decodes the text using the codebook and writes it to file from a string
    output_file.close()


"""Encodes and then decodes a file and checks whether the resulting output was the same as the input"""


def conduct_test(file_name):
    print("Encoding:")
    start_time = time.time()
    encode(file_name)
    print("--- Time Taken: %s seconds ---" % (time.time() - start_time))
    print("\n Decoding: \n")
    start_time = time.time()
    decode(file_name)
    print("--- Time Taken: %s seconds ---" % (time.time() - start_time))
    assert open("InputFiles/" + file_name.split(".")[0] + ".txt", 'rb').read() == open(
        "DecompressedFiles/" + file_name.split(".")[0] + ".txt", 'rb').read()
    print("\n Encoding and Decoding were both successful...")


"""Command Line interface, function called when python file is run"""


def implement():
    file_name = " "
    command = input(""" 
    encode  --  encodes a file from the InputFiles/ directory using a 
                canonical huffman code which is calculated from the 
                frequency of characters in the file. The file is outputed
                with the file_name.hc, which has at the start the codebook
                and then the resulting encoding.

    decode  --  decodes a file from the CompressedFiles/ directory by first
                extracting the codebook from the start of the file and then
                decoding the resulting encryption

    test    --  encodes and then decodes the file and then checks whether the
                input was the same as the output

    quit     -- exits the program, works at any point in the interface

    Please type a valid command: 
    """)

    if command == "encode" or command == "print" or command == "test":
        while not os.path.exists("InputFiles/" + file_name):
            print("\n Pick a valid file from the 'InputFiles' directory")
            find_file = "Which file would you like to " + command + "; please include the extension: "
            for fi in os.listdir("InputFiles/"):
                find_file += "\n " + fi
            file_name = input(find_file + "\n")

            if os.path.exists("InputFiles/" + file_name):
                if command == "encode":
                    start_time = time.time()
                    encode(file_name)
                    print("--- Time Taken: %s seconds ---" % (time.time() - start_time))
                    print("\n Your file has been encoded and is in the 'CompressedFiles' directory")
                    implement()
                elif command == "test":
                    conduct_test(file_name)
                    implement()
            elif file_name == "quit":
                print("Exiting...")
                break
            else:
                print("Come on mate, pick an available option...")

    elif command == "decode":
        while not os.path.exists("CompressedFiles/" + file_name):
            print("Pick a valid file from the 'CompressedFiles' directory")
            find_file = "Which file would you like to, no need to include the extension: "
            for fi in os.listdir("CompressedFiles/"):
                find_file += "\n " + fi
            file_name = input(find_file + "\n")

            if os.path.exists("CompressedFiles/" + file_name + ".hc"):
                start_time = time.time()
                decode(file_name)
                print("--- Time Taken: %s seconds ---" % (time.time() - start_time))
                print("Your file has been decoded and is in the 'DecompressedFiles' directory")
                implement()
            elif file_name == "quit":
                print("Exiting...")
                break
            else:
                print("Come on mate, pick an available option...")
    elif command == "quit":
        print("Exiting...")
    else:
        print("Come on mate, pick an available option...")
        implement()


#implement()

start_time = time.time()
encode("WarAndPeace.txt")
print("--- Time Taken: %s seconds ---" % (time.time() - start_time))
start_time = time.time()
decode("WarAndPeace")
print("--- Time Taken: %s seconds ---" % (time.time() - start_time))

