##########################################################################
#                                                                        #
#  Filename: huffman.py                                                  #
#  Author: Oliver Baxandall                                              #
#  Date created: 28 / 01 / 2018                                          #
#  Date Last-Modified: 14 / 02 / 2018                                    #
#  Python Version: 3.6.4                                                 #
#  Dependicies: Python Standard Library,                                 #
#               bitarray module with a c- interpreter                    #
#  Description: A Program that compresses and decompresses .txt files    #
#               Includes a command line interface for user control...    #
#                                                                        #
##########################################################################

""" All part of the python standard library except bitarray:
    can be installed using 'pip3 install bitarray' """
import time
import os.path
import heapq as heap
from operator import itemgetter
from bitarray import bitarray


class Node(object):
    """ A class for the nodes of the huffman tree.
    Each node has a character value, a frequency (the number of times it appears in the file),
    a left and a right child. Each of the children are new nodes or are 'None' in the leaf case """

    def __init__(self, value, frequency):
        self.left = None
        self.right = None
        self.value = value
        self.frequency = frequency

    def __lt__(self, other):
        """a comparative function: compares the frequency of the node with another.
        Primarily used when creating the heap..."""
        return self.frequency < other.frequency

    def set_children(self, left, right):
        """set children of the current node"""
        self.left = left
        self.right = right


def write_code_lengths(current_node, code_size, code_lengths):
    """ A function that recursively calls itself. Creates a list of tuples 'code_lengths',
    which details the character value and the length of the huffman code.
    For this version, code_book creation is canonical, so computation time is saved by not
    calculating the code, only the length that it would be given the tree.
    The resulting code_book is generated and returned as a dictionary """

    if current_node.value is not None:  # if a leaf, the node.value is not 'None'
        code_lengths[current_node.value] = code_size
    # expands out and calls the function for the nodes children
    else:  # calls the function again
        write_code_lengths(current_node.left, code_size + 1, code_lengths)
        write_code_lengths(current_node.right, code_size + 1, code_lengths)


def write_code_book(ordered_code_lengths):
    """ Generates a canonical code from a list of tuples (character, length),
    ordered by code length and then alphabetically,
    returns a code_book as a list of tuples (char, binary_code) that is sorted character value"""

    code_book = []
    current_length = ordered_code_lengths[0][1]  # sets the inital start length
    code_int = 0

    for char_length in ordered_code_lengths:
        # bit shifts the number of times that the current length differs from the previous
        code_int = code_int << (char_length[1] - current_length)
        current_length = char_length[1]  # resets the length
        # converts the integer value to binary with the correct bit length
        code = format(code_int, "0" + str(current_length) + "b")
        code_book.append((char_length[0], code))  # adds the new code to the list
        code_int += + 1

    code_book.sort()  # sorts the code_book list into by the first value, alphabetically
    return code_book


def code_book_output_canonical(code_book_list):
    """Writes the code_book as a canonically to a binary string for file.
    This means writing a list of lengths for each code from 1 to 256, with 0 being an unused
    for example: (0,0,0,0,0,0,0,0,0,6,11,2,3,4 ...)"""

    code_book_output = ""
    previous_val = 0
    for char_length in code_book_list:
        for _ in range(previous_val, char_length[0] - 1):
            code_book_output += "0"  # adds zeros' if a length for the character is not available
        previous_val = char_length[0]
        code_book_output += "1"  # adds a zero if length is available, length presented next
        code_book_output += format(len(char_length[1]), "06b")  # converts the length to binary
    for _ in range(previous_val, 256):
        code_book_output += "0"
    return code_book_output


def code_book_output_tradition(code_book_list):
    """ Writes the code_book in a simpler form, showing the code length and then the character
    for example, (2,A,5,B,5,D). Written in order of lengths and then alphabetically """
    code_book_output = ""
    for char_length in code_book_list:
        code_book_output += format(char_length[0], "08b")
        code_book_output += format(len(char_length[1]), "04b")
    return code_book_output


def encode(filename, directory):  # compress the file
    """ Compresses a file into a smaller version with extension '.hc',
     from the InputFiles/ directory """

    start = time.time()
    print(filename)
    input_file = open("InputFiles/" + directory + "/" + filename,
                      "rb")  # opens the file from the InputFiles directory
    input_size = os.path.getsize(
        "InputFiles/" + directory + "/" + filename)  # finds the input size for later comparison
    data = input_file.read()  # assigns the data as a bytes variable

    frequencies = {}  # dictionary of each character and its relative frequency
    for character in data:
        if character in frequencies.keys():  # if the character x is already a key
            frequencies[character] += 1
        else:  # therefore x is not a key yet
            frequencies[character] = 1

    node_list = []
    # creates a list of all nodes for each character
    for val, freq in frequencies.items():
        added_node = Node(val, freq)
        node_list.append(added_node)

    # The heap stores everything in reverse order to start,
    # collects up nodes and then adds them back on to the heap
    # uses the heap module to do this as efficiently as possible
    heap.heapify(node_list)

    while len(node_list) > 1:  # while the heap still has a root
        right = heap.heappop(node_list)  # heappop returns the smallest value
        left = heap.heappop(node_list)
        new_node = Node(
            None, right.frequency + left.frequency)  # therefore only the leaves have a data value
        new_node.set_children(left, right)
        heap.heappush(node_list, new_node)  # updates the heap
    root = node_list[0]  # now node_list contains only the root with all others extending

    code_lengths = {}  # dictionary of the code lengths for each character
    write_code_lengths(root, 0, code_lengths)
    ordered_code_lengths = sorted(
        code_lengths.items(), key=itemgetter(1, 0))  # convert to ordered tuple for canonical
    code_book_list = write_code_book(
        ordered_code_lengths)  # converts the code_lengths to canonical code
    code_book_dict = {}  # creates the code_book as a dictionary for the bitarray encode function
    for i in code_book_list:
        code_book_dict[i[0]] = bitarray(i[1])

    output_file = open("CompressedFiles/" + directory + "/" + filename.split(".")[0] + ".hc", "wb")

    # writes the code lengths to the start of the file, starts as a string
    output_can = code_book_output_canonical(code_book_list)
    output_trad = code_book_output_tradition(code_book_list)
    if len(output_can) > len(output_trad):
        code_book_output = "0" + format(len(output_trad), "011b") + output_trad
    else:
        code_book_output = "1" + output_can
    book_list = bitarray(code_book_output)  # converts to bitarray
    book_add = book_list.buffer_info()[3]
    book_add_binary = format(book_add, "08b")  # add is short for additional
    book_list = bitarray(bitarray(
        book_add_binary + "0" * book_add) + book_list)  # adds zeros to ensure multiple of 8
    book_list.tofile(output_file)  # writes the code_book to the file

    text_list = bitarray(endian="little")
    text_list.encode(code_book_dict, data)  # text list is a bitarray of the text encoded
    text_add = text_list.buffer_info()[3]  # finds the number of unused bits to match it up to 8
    text_add_binary = format(text_add, "08b")  # appends this number of 0's
    text_list = bitarray(
        bitarray(text_add_binary + "0" * text_add) + text_list)  # ensures multiple of 8
    text_list.tofile(output_file)
    output_file.close()

    output_size = os.path.getsize(
        "CompressedFiles/" + directory + "/" + filename.split(".")[
            0] + ".hc")  # size of output file

    if output_size > input_size:
        output_file.close()
        print("Your file cannot be compressed any further so has been left as a txt file")

    print("\nOutput Size: " + str(output_size) + " bits")
    print("Input Size: " + str(input_size) + " bits")
    print("------------> Compression Ratio: " + str(input_size / output_size) + "\n")

    # used when collecting data for analysis
    # print(str(input_size) + " " + str(output_size) + " " + str(time.time() - start) + " " +
    #     str(input_size / output_size) + " " + str(len(frequencies)))


def decode(filename, output_extension):
    """Decompresses a file with the extension '.hc',
    from the CompressedFiles/ directory into a '.txt' file """

    input_file = open("CompressedFiles/" + filename.split(".")[0] + ".hc",
                      "rb")  # reads the file in binary
    data = input_file.read()
    # converts the bytes to bits in 8 bit form, allocating it to one long string
    code = ""
    for i in data:
        code += format(i, "08b")

    # extracts the code_book
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
        for code_length in binary_lengths:
            lengths.append(int(code_length, 2))

        # gets rid of the 0's and makes a list of tuples with the character and the codeword length
        for i in range(0, 255):  # 255 because of list indexing
            if lengths[i] != 0:
                ordered_codelengths.append((i + 1, lengths[i]))
    else:
        code_book_length = int(code[:11], 2) + 11
        code_book_string = code[11:code_book_length]
        code = code[code_book_length:]
        while code_book_string:
            ordered_codelengths.append(
                (int(code_book_string[:8], 2), int(code_book_string[8:12], 2)))
            code_book_string = code_book_string[12:]

    # engineers the code_book from the ordered_codelengths as performed in encoding
    code_book_list = write_code_book(sorted(ordered_codelengths, key=itemgetter(1, 0)))
    code_book_dict = {}
    for i in code_book_list:
        code_book_dict[chr(i[0])] = bitarray(i[1])  # converts to characters for decoding

    text_buffer = int(code[0:8], 2) + 8  # gets rid of the buffer created when the text is added
    code = code[text_buffer:]
    output_file = open("DecompressedFiles/" + filename.split(".")[0] + output_extension, "w")
    text = bitarray(code)
    output_file.write(''.join(text.decode(
        code_book_dict)))  # decodes the text from code_book and writes it to file as a string
    output_file.close()


def conduct_test(filename):
    """ Encodes and then decodes a file and checks whether the output is the same as the input """

    print("Encoding:")
    start_time = time.time()
    encode(filename, "")
    print("--- Time Taken: %s seconds ---" % (time.time() - start_time))
    print("\n Decoding: \n")
    start_time = time.time()
    decode(filename, ".txt")
    print("--- Time Taken: %s seconds ---" % (time.time() - start_time))
    assert open("InputFiles/" + filename.split(".")[0] + ".txt", 'rb').read() == open(
        "DecompressedFiles/" + filename.split(".")[0] + ".txt", 'rb').read()
    print("\n Encoding and Decoding were both successful...")


def compress_directory(directory_name):
    if not os.path.exists("CompressedFiles/" + directory_name):
        os.makedirs("CompressedFiles/" + directory_name)
    for input_file in os.listdir("InputFiles/" + directory_name):
        encode(input_file, directory_name)


def implement():
    """ Command Line Interface for the control of encoding and decoding files """

    filename = " "
    command = input("""
    encode: encodes a file from the InputFiles/ directory using a 
            canonical huffman code which is calculated from the 
            frequency of characters in the file. The file is outputed
            with the filename.hc, which has at the start the code_book
            and then the resulting encoding.
    
    decode: decodes a file from the CompressedFiles/ directory by first
            extracting the code_book from the start of the file and then
            decoding the resulting encryption

    test:   encodes and then decodes the file and then checks whether the
            input file is the same as the output file
            
    compress folder: Takes a folder from the InputFiles/ directory and
            compresses every folder inside it and subsequently places the
            files in a directory under the same name in CompressedFiles/
            directory
                
    quit:   exits the program, works at any point in the interface

    Please type a valid command: 
    """)

    if command == "encode" or command == "print" or command == "test":
        while not os.path.exists("InputFiles/" + filename):
            print("\n Pick a valid file from the 'InputFiles' directory")
            find_file = "Which file would you like to " + \
                        command + "; please include the extension: "
            for input_file in os.listdir("InputFiles/"):
                find_file += "\n " + input_file
            filename = input(find_file + "\n")

            if os.path.exists("InputFiles/" + filename):
                if command == "encode":
                    start_time = time.time()
                    encode(filename, "")
                    print("--- Time Taken: %s seconds ---" % (time.time() - start_time))
                    print("\n Your file has been encoded and is in the 'CompressedFiles' directory")
                    implement()
                elif command == "test":
                    conduct_test(filename)
                    implement()
            elif filename == "quit":
                print("Exiting...")
                break
            else:
                print("Come on, pick an available option...")

    elif command == "compress folder":
        while not os.path.exists("InputFiles/" + filename):
            print("\n Pick a valid folder or single file from the 'InputFiles' directory")
            find_file = "Which folder would you like to compress"
            for input_file in os.listdir("InputFiles/"):
                find_file += "\n " + input_file
            folder = input(find_file + "\n")
            if os.path.exists("InputFiles/" + folder):
                compress_directory(folder)
            else:
                print("Come on, pick an available option...")
        implement()

    elif command == "decode":
        while not os.path.exists("CompressedFiles/" + filename):
            print("Pick a valid file from the 'CompressedFiles' directory")
            find_file = "Which file would you like to, no need to include the extension: "
            for input_file in os.listdir("CompressedFiles/"):
                find_file += "\n " + input_file
            filename = input(find_file + "\n")

            if os.path.exists("CompressedFiles/" + filename + ".hc"):
                start_time = time.time()
                decode(filename, ".txt")
                print("--- Time Taken: %s seconds ---" % (time.time() - start_time))
                print("Your file has been decoded and is in the 'DecompressedFiles' directory")
                implement()
            elif filename == "quit":
                print("Exiting...")
                break
            else:
                print("Come on, pick an available option...")
    elif command == "quit":
        print("Exiting...")
    else:
        print("Come on, pick an available option...")
        implement()


implement()
