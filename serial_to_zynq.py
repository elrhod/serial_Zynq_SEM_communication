import serial
import argparse
import re
from typing import List
import time
import csv
import os

PROJECT_DIR = "C:\\Users\\Eduardo\\PycharmProjects\\serial\\"
OUTPUT_DIR = PROJECT_DIR + 'outputs\\'
OUTPUT_RAW_DIR = OUTPUT_DIR + 'raw\\'


def get_input_parameters(inp_par):
    # Initialize parser
    parser = argparse.ArgumentParser()

    # Adding optional argument
    parser.add_argument("-i", "--input", help="input EDB file from Vivado.")

    args = vars(parser.parse_args())
    # Read arguments from command line
    return args[inp_par]


def read_lines_with_essentialbits_from_list_of_files(list_of_files_file):
    file_list = []
    lines_with_essentialbits = []
    radix_name = []
    with open(list_of_files_file, "r") as f:
        for line in f:
            file_list.append(line)

    for each_file in file_list:
        st1 = each_file.rsplit("\\", 1)[1].rsplit(".")[0] + str(".txt")

        print(st1)

        print(OUTPUT_DIR + st1)

        try:
            wf = open(OUTPUT_DIR + st1, "w")
        except FileNotFoundError:
            print("File not found or path is incorrect")
        finally:
            print("File opened!")

        print(each_file)
        line_cnt = 0
        with open(each_file.rstrip("\n"), "r") as f2:
            each_file_lines_with_essentialbits = []
            for _ in range(8):
                next(f2)
            for line in f2:
                line_cnt += 1
                if line != "00000000000000000000000000000000\n":
                    wf.writelines(str(line_cnt) + " " + line)
                    # wf.writelines(str(line_cnt) + " " + line + "\n")
                    each_file_lines_with_essentialbits.append((line_cnt, line))
                    # print(line)
                    # input('Press any key')

            lines_with_essentialbits.append(each_file_lines_with_essentialbits)
            radix_name.append(st1)

    wf.close()

    return lines_with_essentialbits, radix_name


def subtract_lists(list_of_lines_with_essentialbits):
    """
    :param list_of_lines_with_essentialbits  (does the subtraction only for the first 2 lists):
    List of lists of essential bit lines of files read.
    :return: list subtraction. Ex.:
    x = [1,2,3,4,5,6,7,8,9,0]   {item 0 of list}
    y = [1,3,5,7,9]             {item 1 of list}
    x - y = [2,4,6,8,0]
    """

    result = []
    result = [item for item in list_of_lines_with_essentialbits[1] if item not in list_of_lines_with_essentialbits[0]]
    print(result)
    return result


def compare_two_list_and_return_different_EBs(list_of_lines_with_essentialbits):
    """
    :param list_of_lines_with_essentialbits  (compare only the first 2 lists):
    if line number is present in "the complete" file only, then it is captured.
    if line number is present in both files, then the content is compared to see if there is different bits at that line
     to be captured

    :return: list of different lines and bits.
    Ex.:

    """
    dic = dict(list_of_lines_with_essentialbits[1])
    different_lines_and_EBs = []
    for line_number, essential_bits in list_of_lines_with_essentialbits[0]:
        if (line_number in dic):
            other_EB = dic.get(line_number)
            if (essential_bits != other_EB):
                new_EB = ""
                print("EBs diferentes na mesma linha presentes nas duas listas!")
                print(essential_bits)
                print(dic.get(line_number))
                for x, y in zip(essential_bits, other_EB):
                    if (x == "1" and y == "0"):
                        new_EB += "1"
                    elif (x != "\n"):
                        new_EB += "0"
                print(new_EB)
                # input('Press any key 1')
                if (new_EB != "00000000000000000000000000000000"):
                    different_lines_and_EBs.append((line_number, new_EB))
        else:
            print("Linha presente apenas no completo:")
            print(line_number, essential_bits)
            # input('Press any key 2')
            different_lines_and_EBs.append((line_number, essential_bits.rstrip("\n")))

    return different_lines_and_EBs


def write_list_to_file(file, my_list):
    with open(file, 'w+') as f:
        for item in my_list:
            f.write("%d\n" % item)


def write_list_str_to_file(file, my_list):
    with open(file, 'w+') as f:
        for item in my_list:
            f.write("%s\n" % item)


def write_list_of_str_list_to_file(file, my_list):
    with open(file, 'w+') as f:
        for list1 in my_list:
            for item in list1:
                f.write("%s\n" % item)

# def write_list_of_tuple_to_file(file, mylist):
#     with open(file, 'w') as fp:
#         fp.write('\n'.join('%s %s' % x for x in mylist))


def write_list_of_tuple_to_file(file, mylist):
    with open(file, 'w', newline='', encoding='utf-8') as fp:
        csv.register_dialect("custom", delimiter=" ", skipinitialspace=True)
        writer = csv.writer(fp, dialect="custom")
        for tup in mylist:
            writer.writerow(tup)


def get_essential_bits(component_numbers):

    list_of_fault_injection_list = []

    # open file
    inp = get_input_parameters("input")

    print(inp)
    list_of_lines_with_essentialbits, radix_name = read_lines_with_essentialbits_from_list_of_files(inp)
    print(list_of_lines_with_essentialbits)

    for num in component_numbers:
        list_to_sub1 = [list_of_lines_with_essentialbits[num], list_of_lines_with_essentialbits[0]]

        diff1 = compare_two_list_and_return_different_EBs(list_to_sub1)
        print(diff1)

        write_list_of_tuple_to_file("Essential_bits_Comp" + str(num) + "_Only.txt", diff1)
        list_of_fault_injection_list.append(diff1)


    list_size = len(list_of_fault_injection_list)
    for i in range(list_size):
        fault_injection_list = []

        for line_number, e_bit in list_of_fault_injection_list[i]:
            for z in range(len(e_bit)):
                if e_bit[z]=="1":
                    query_command, word = gen_Query_command(line_number, 31-z)
                    fi_comm = gen_FI_command(line_number, 31-z)
                    fault_injection_list.append((query_command, fi_comm, word, 31-z))

        write_list_of_tuple_to_file("Fault_Injection_Comp" + str(i) + ".txt", fault_injection_list)


    list_size = len(list_of_fault_injection_list)
    for i in range(list_size):
        resultant_list = []
        fault_injection_list = []
        for j in range(list_size):
            if i != j:
                if len(resultant_list)==0:
                    lists_to_compare = [list_of_fault_injection_list[i], list_of_fault_injection_list[j]]
                else:
                    lists_to_compare = [resultant_list, list_of_fault_injection_list[j]]
                resultant_list = compare_two_list_and_return_different_EBs(lists_to_compare)

        for line_number, e_bit in resultant_list:
            for z in range(len(e_bit)):
                if e_bit[z]=="1":
                    query_command, word = gen_Query_command(line_number, 31-z)
                    fi_comm = gen_FI_command(line_number, 31-z)
                    fault_injection_list.append((query_command, fi_comm, word, 31-z))

        write_list_of_tuple_to_file("Fault_Injection_Comp" + str(i) + "_Only.txt", fault_injection_list)

    return list_of_fault_injection_list


def serial_init(port, baundrate, timeout):
    return serial.Serial(port, baundrate, timeout=timeout)


def serial_loop(ser):
    while True:
        txt = input("Type something to send or 'R' to receive or 'X' to quit: ")
        if (txt == "x" or txt == "X"):
            break
        elif (txt == "r" or txt == "R"):
            line = ser.readline()  # read a '\n' terminated line
            if len(line) > 0:
                spt = line.split(b'\r')
                for elem in spt:
                    print(elem)
                # print(spt)
        else:
            ser.write(txt.encode('utf-8'))
            print(txt.encode('utf-8'))


def serial_command(ser, command):
    """

    :rtype: object
    """
    spt=[]
    if (command == "r" or command == "R"):
        line = ser.readline()  # read a '\n' terminated line
        if len(line) > 0:
            print("Read:" + str(line))
            spt = line.split(b'\r')
            for elem in spt:
                print(elem.decode('utf-8'))
    else:
        ser.write(command.encode('utf-8'))
        print(command.encode('utf-8'))

    return spt


def wait_for_msg(ser, msg):
    print("Waiting for Message: " + msg)
    done = False

    line = ""
    while not done:
        line = read_bytes_from_SEM(ser)  # read all the buffer
        # print(len(line))
        if len(line) > 0:
            print(line)
            if line.decode(encoding='utf-8').find(msg) != -1:
                done = True
            # else:
            #     print(line)
        # time.sleep(1)


def get_all_msg_until_text(ser, msg):
    print("Waiting for Message: " + msg)
    done = False
    complete_msg = bytearray()
    words_read = []
    while not done:
        line = read_bytes_from_SEM(ser)  # read all the buffer
        # line = ser.readline()  # read a '\n' terminated line
        if len(line) > 0:
            complete_msg.extend(line)
            print(line)
            # print("line:")
            # print(line)
            words_read = line.split(b'\r')

            if complete_msg.find(msg.encode(encoding='utf-8')) != -1:
                done = True
            # else:
            #     print(line)
        # time.sleep(1)
        else:
            time.sleep(0.1)


    print(complete_msg.split(b'\r'))
    # print(len(words_read))
    return complete_msg.split(b'\r')


def gen_FI_command(line_number, bit):
    words_per_frame = 93
    real_line = line_number - 26  # there are 25 dummy words at the begining of the EBD file for ULTRASCALE+ devices and -1 so first line number becomes 0
    word = real_line % words_per_frame
    # print ("word: " + str(word))
    frame = int((real_line - word) / words_per_frame - 1)
    # print ("frame: " + str(frame))
    decim = (12 * (2 ** 40)) + (frame * (2 ** 12)) + (word * (2 ** 5) + bit)
    # print ("decim: " + str(decim))
    hexa = hex(int(decim))
    # print(hexa)
    # add "N ", remove "0x and make upper case
    upper_case = ('N ' + hexa[2:]).upper()
    # bin_encode = upper_case.encode('utf-8')
    # print(bin_encode)
    return upper_case


def gen_Query_command(line_number, bit):
    words_per_frame = 93
    real_line = line_number - 26  # there are 25 dummy words at the begining of the EBD file for ULTRASCALE+ devices and -1 so first line number becomes 0
    word = real_line % words_per_frame
    print ("word: " + str(word))
    frame = int((real_line - word) / words_per_frame - 1)
    print ("frame: " + str(frame))
    decim = (12 * (2 ** 40)) + (frame * (2 ** 12)) + (word * (2 ** 5) + bit)
    print ("decim: " + str(decim))
    hexa = hex(int(decim))
    print(hexa)
    # add "N ", remove "0x and make upper case
    upper_case = ('Q ' + hexa[2:]).upper()
    bin_encode = upper_case.encode('utf-8')
    print(bin_encode)
    return upper_case, word


def gen_Query_command_from_frame(frame):
    bit = 0
    word = 0
    # print ("frame: " + str(frame))
    decim = (12 * (2 ** 40)) + (frame * (2 ** 12)) + (word * (2 ** 5) + bit)
    # print ("decim: " + str(decim))
    hexa = hex(int(decim))
    print(hexa)
    # add "N ", remove "0x and make upper case
    upper_case = ('Q ' + hexa[2:]).upper()
    bin_encode = upper_case.encode('utf-8')
    print(bin_encode)
    return upper_case, word


def read_bytes_from_SEM(ser):
    done = False
    r = ""
    while not done:
        if ser.in_waiting > 0:
            r = ser.read(ser.in_waiting)
            done = True
            # print(r)
    return r


def compare_lists(l1, l2, word, bit):
    f = open('compare_report3.txt', 'a')

    if len(l1) == 93 and len(l2) == 93:
        # if(l1==l2):
        #     print("Lists are identical")
        # else:
        #     print("Lists are Different:")
        #     # Find the index at which the element of two list doesn't match.
        #     # Using list comprehension and zip
        #     Output = []
        #     for x, y in zip(l1, l2):
        #         if y != x:
        #             Output.append(l2.index(y))
        #
        #     print(Output)
        num1 = int(l2[word].decode('utf-8'),16)
        num2 = int(l1[word].decode('utf-8'),16)
        if (num1 >= num2):
            dif = num1 - num2
        else:
            dif = num2 - num1

        if dif == 0:
            f.write("Lists are identical:\n")
        else:
            if dif == (2**bit):
                f.write("Lists are Different: Bit Matches!\n")
            else:
                f.write("Different Bits! Word: %d Bit: %d Berfore:%08x  After:%08x \n" % (word, bit, int(l1[word].decode('utf-8'),16), int(l2[word].decode('utf-8'),16)))
                print(l2[word])
                print(l1[word])
                print("word:" + str(word))
                print("bit:" + str(bit))
                exit()
    else:
        print("Data out of format")
        exit()

    f.close()


def start_fault_injection2(essential_bits_list, serial):
    word = 51
    bit = 2
    tempo=0.01
    tempo2=2
    txt = input("Type something to send or 'R' to receive or 'X' to quit: ")
    serial_command(serial,"R")
    time.sleep(tempo)
    serial_command(serial,"R")
    serial_command(serial,"R")
    serial_command(serial,"R")
    serial_command(serial,"I")
    time.sleep(tempo*2)
    serial_command(serial, "R")
    serial_command(serial, "R")
    serial_command(serial, "Q C0001AC7662")
    time.sleep(tempo*10)
    l1 = serial_command(serial,"R")
    serial_command(serial, "Q C0001AC7662")
    time.sleep(tempo*10)
    l3 = serial_command(serial,"R")
    compare_lists(l1[1:-1], l3[1:-1], word, bit)
    serial_command(serial, "N C0001AC7662")
    time.sleep(tempo*2)
    serial_command(serial, "R")
    serial_command(serial,"Q C0001AC7662")
    time.sleep(tempo*10)
    l2 = serial_command(serial,"R")
    compare_lists(l1[1:-1],l2[1:-1], word, bit)
    time.sleep(tempo)
    serial_command(serial,"R")
    serial_command(serial,"O")
    time.sleep(tempo*10)
    serial_command(serial,"R")


def start_fault_injection(essential_bits_list, serial):
    # read_bytes_from_SEM(serial)
    # print(serial.in_waiting)

    # wait_for_msg(serial, "Xilinx Zynq MP First Stage Boot Loader")
    # wait_for_msg(serial, "INIT_DONE")
    # print("Zynq Initialization Done!!!")
    wait_for_msg(serial, "O> ")
    print("SEM Initialization Done!!!")
    serial.write(b'I\n')
    wait_for_msg(serial, "I> ")
    print("SEM Idle!!!")

    # for line_number, essential_bits in essential_bits_list:
    #     for i in range(len(essential_bits)):
    #         if essential_bits[i] == "1":
    #             FI_command = gen_FI_command(line_number, i)

    # serial.write(b'regs\n')
    print("-----------------------------------------------")
    serial.write(b'N C0001AC7662\n')
    print(get_all_msg_until_text(serial, "I> "))
    # time.sleep(1)
    # serial.write(b'Q C0001AC7662\n')
    # get_all_msg_until_text(serial, "I> ")
    # print("-1----------------------------------------------")
    # # time.sleep(1)
    # serial.write(b'Q C0001AC7662\n')
    # get_all_msg_until_text(serial, "I> ")
    # print("-2----------------------------------------------")
    # # time.sleep(1)
    # serial.write(b'Q C0001AC7662\n')
    # get_all_msg_until_text(serial, "I> ")
    print("-3----------------------------------------------")
    # time.sleep(1)
    serial.write(b'O\n')
    get_all_msg_until_text(serial, "COR")


def read_file_to_list(path):
    prj_path = os.getcwd()
    file_path = prj_path + "\\" + path
    print(file_path)
    l = []
    with open(file_path) as f:
        lines = f.read().splitlines()


    return lines


def start_fault_injection3(essential_bits_list, serial):
    f = open('report.txt', 'w')
    f.close()
    tempo=0.01
    txt = input("Press any key to continue!")
    serial_command(serial,"R")
    time.sleep(tempo)
    serial_command(serial,"R")
    serial_command(serial,"R")
    serial_command(serial,"R")
    serial_command(serial,"R")

    for query_com, fi_comm, word, bit in essential_bits_list:
        serial_command(serial, "I")
        time.sleep(tempo * 2)
        serial_command(serial, "R")
        serial_command(serial, query_com)
        time.sleep(tempo * 9)
        l1 = serial_command(serial, "R")
        serial_command(serial, fi_comm)
        time.sleep(tempo * 2)
        serial_command(serial, "R")
        serial_command(serial, query_com)
        time.sleep(tempo * 9)
        l2 = serial_command(serial, "R")
        compare_lists(l1[1:-1], l2[1:-1], word, bit)
        # txt = input("Press any key to continue!")


def start_fault_injection4(essential_bits_list, serial):
    f = open('report2.txt', 'w')
    f.close()
    tempo=0.01
    txt = input("Press any key to continue!")
    serial_command(serial,"R")
    time.sleep(tempo)
    serial_command(serial,"R")
    serial_command(serial,"R")
    serial_command(serial,"R")
    serial_command(serial,"R")

    for query_com, fi_comm, word, bit in essential_bits_list:
        serial_command(serial, "I")
        time.sleep(tempo * 2)
        serial_command(serial, "R")
        serial_command(serial, query_com)
        time.sleep(tempo * 9)
        l1 = serial_command(serial, "R")
        serial_command(serial, fi_comm)
        time.sleep(tempo * 2)
        serial_command(serial, "R")
        serial_command(serial, "O")
        time.sleep(tempo * 5)
        serial_command(serial, "R")
        serial_command(serial, "I")
        time.sleep(tempo * 2)
        serial_command(serial, "R")
        serial_command(serial, query_com)
        time.sleep(tempo * 9)
        l2 = serial_command(serial, "R")
        compare_lists(l1[1:-1], l2[1:-1], word, bit)
        # txt = input("Press any key to continue!")


def start_fault_injection5(essential_bits_list, serial):
    f = open('report3.txt', 'a')
    f.close()
    tempo=0.01
    txt = input("Press any key to continue!")
    serial_command(serial,"R")
    time.sleep(tempo)
    serial_command(serial,"R")
    serial_command(serial,"R")
    serial_command(serial,"R")
    serial_command(serial,"R")

    for query_com, fi_comm, word, bit in essential_bits_list:
        f = open('report3.txt', 'a')
        serial_command(serial, "I")
        time.sleep(tempo * 5)
        serial_command(serial, "R")
        serial_command(serial, query_com)
        time.sleep(tempo * 25)
        l1 = serial_command(serial, "R")
        serial_command(serial, fi_comm)
        time.sleep(tempo * 5)
        serial_command(serial, "R")
        serial_command(serial, "Z")
        time.sleep(tempo * 30)
        report = serial_command(serial, "R")
        f.write("%s\n" % report)
        serial_command(serial, "O")
        time.sleep(tempo * 10)
        serial_command(serial, "R")
        serial_command(serial, "I")
        time.sleep(tempo * 5)
        serial_command(serial, "R")
        serial_command(serial, query_com)
        time.sleep(tempo * 15)
        l2 = serial_command(serial, "R")
        compare_lists(l1[1:-1], l2[1:-1], word, bit)
        # txt = input("Press any key to continue!")

        f.close()


def start_fault_injection6(essential_bits_list, serial, report_file):
    f = open(report_file, 'a')
    f.close()
    tempo=0.1
    txt = input("Press any key to continue!")
    serial_command(serial,"R")
    time.sleep(tempo)
    serial_command(serial,"R")
    serial_command(serial,"R")
    serial_command(serial,"R")
    serial_command(serial,"R")
    serial_command(serial, "I")
    get_all_msg_until_text(serial, "I>")
    # query_com, fi_comm, word, bit = essential_bits_list[0]
    for line in essential_bits_list:
        qc1, qc2, fc1, fc2, word, bit = line.split()
        query_com = qc1 + " " + qc2
        fi_comm = fc1 + " " + fc2
        f = open(report_file, 'a')
        serial_command(serial, query_com)
        l1 = get_all_msg_until_text(serial, "I>")
        serial_command(serial, fi_comm)
        get_all_msg_until_text(serial, "I>")
        serial_command(serial, "Z")
        report = get_all_msg_until_text(serial, "END")
        f.write("%s %s %s %s\n" % (report, fi_comm, word, bit))
        serial_command(serial, "O")
        time.sleep(tempo)
        # get_all_msg_until_text(serial, "O>")
        get_all_msg_until_text(serial, "COR")
        serial_command(serial, "I")
        get_all_msg_until_text(serial, "I>")
        serial_command(serial, query_com)
        l2 = get_all_msg_until_text(serial, "I>")
        compare_lists(l1[1:-1], l2[1:-1], int(word), int(bit))
        # txt = input("Press any key to continue!")

        f.close()


def start_fault_injection7(essential_bits_list, serial, report_file):
    f = open(report_file, 'a')
    f.close()
    tempo=0.1
    txt = input("Press any key to continue!")
    serial_command(serial,"R")
    time.sleep(tempo)
    serial_command(serial,"R")
    serial_command(serial,"R")
    serial_command(serial,"R")
    serial_command(serial,"R")
    serial_command(serial, "I")
    get_all_msg_until_text(serial, "I>")
    # query_com, fi_comm, word, bit = essential_bits_list[0]
    for line in essential_bits_list:
        qc1, qc2, fc1, fc2, word, bit = line.split()
        query_com = qc1 + " " + qc2
        fi_comm = fc1 + " " + fc2
        f = open(report_file, 'a')
        serial_command(serial, query_com)
        l1 = get_all_msg_until_text(serial, "I>")
        serial_command(serial, fi_comm)
        get_all_msg_until_text(serial, "I>")
        serial_command(serial, "Z")
        report = get_all_msg_until_text(serial, "END")
        f.write("%s %s %s %s\n" % (report, fi_comm, word, bit))
        # txt = input("Press any key to continue!")
        f.close()


def S_loop(serial):
    tempo=0.1
    tempo2=0.5
    txt = input("Press any key to continue!")
    serial_command(serial,"S")
    time.sleep(tempo)
    while True:
        serial_command(serial,"S")
        time.sleep(0.05)
        # serial_command(serial,"O")
        # time.sleep(tempo2)


def read_ebc_file(ebc_file_name):
    line_cnt=0
    ebc_list=[]
    with open(ebc_file_name, "r") as f2:
        each_file_line = []
        for _ in range(8):
            next(f2)
        for line in f2:
            line_cnt += 1
            line_hex = hex(int(line,2))
            print(line)
            print(line_hex[2:].zfill(8))
            ebc_list.append(line_hex[2:].zfill(8))
            # input('Press any key')

    return ebc_list


def read_ebd_file(ebd_file_name):
    line_cnt=0
    ebc_list=[]
    with open(ebd_file_name, "r") as f2:
        each_file_line = []
        for _ in range(8):
            next(f2)
        for line in f2:
            line_cnt += 1
            line_hex = hex(int(line,2))
            print(line)
            print(line_hex[2:].zfill(8))
            ebc_list.append(line_hex[2:].zfill(8))
            # input('Press any key')

    return ebc_list


def read_from_sem(serial):
    list_from_sem = []

    max_frame_number = int("ACF1", 16)
    # max_frame_number = int("00F1", 16)
    txt = input("Press any key to continue!")
    serial_command(serial,"R")
    serial_command(serial,"R")
    serial_command(serial,"R")
    serial_command(serial,"R")
    serial_command(serial,"R")
    serial_command(serial, "I")
    get_all_msg_until_text(serial, "I>")
    for frame_number in range(max_frame_number+1):
        print("Reading frame: %d"%1)
        qc, w = gen_Query_command_from_frame(frame_number)
        print(qc)
        serial_command(serial, qc)
        l2=[]
        l1 = get_all_msg_until_text(serial, "I>")
        for li in l1[1:-1]:
            l2.append(li.decode("utf-8"))
        print(l1)
        list_from_sem.append(l2)

    return(list_from_sem)


def compare_EB_lists(ebd, ebc, sem):
    if len(ebc) != len(sem) or len(ebc) != len(ebd):
        print("Lists have different sizes!")
        print(len(ebc))
        print(len(sem))
        quit()
    else:
        for i in range (len(sem)):
            if (int(ebc[i], 16) & int(ebd[i], 16)) != (int(sem[i], 16) & int(ebd[i], 16)):
                print("Line %d have different values! %s %s %s" % (i, ebd[i], ebc[i], sem[i]))


def main_serial():

    ser = serial_init('COM9', 115200, timeout=0)
    S_loop(ser)

    # ebd_list = read_ebd_file("C:\\Users\\Eduardo\\Vivado_Proj\\Emulation_Fow_Projects\\Validation_with_B12\\complete_design.ebd")
    # write_list_str_to_file("ebd_list.txt",ebd_list)

    # ebc_list = read_file_to_list("ebc_list.txt")
    # sem_list = read_file_to_list("list_read_from_sem.txt")
    #
    # print(len(ebc_list))
    # print(len(sem_list))
    #
    # compare_EB_lists(ebd_list[118:-93], ebc_list[118:-93], sem_list)

    # quit()

    # ebc_list = read_ebc_file("C:\\Users\\Eduardo\\Vivado_Proj\\Emulation_Fow_Projects\\Validation_with_B12\\complete_design.ebc")
    # write_list_str_to_file("ebc_list.txt",ebc_list)
    # print(len(ebc_list))

    # serial_loop(ser)

    # list_read_from_sem = read_from_sem(ser)
    # write_list_of_str_list_to_file("list_read_from_sem.txt",list_read_from_sem)
    # txt = input("Press any key to continue!")

    ###################################################################################################################
    ########### SELECT HERE THE SOURCE OF FAULT INJECTION :: DOUBLE CHECK IF THIS IS WHAT YOU WANT

    # fault_injection_list = get_essential_bits([1, 2, 3])
    fault_injection_list = read_file_to_list("Fault_Injection_Comp0.txt")
    txt = input("Press any key to Start Fault Injection!")

    ###################################################################################################################

    # serial_loop(ser);
    # start_fault_injection2(essential_bits, ser)
    # start_fault_injection4(fault_injection_list, ser)
    # start_fault_injection6(fault_injection_list, ser)
    start_fault_injection6(fault_injection_list[12092:], ser, "UpCnt_ErrDetec_Comp0_FULL_2_1000us.txt")
    # start_fault_injection6(fault_injecti  on_list[1838:], ser, "b12_retry_Comp0_0_100us_1838.txt")
    # start_fault_injection6(fault_injection_list[3506:], ser, "b12_retry_Comp0_0_100us_3506.txt")
    # start_fault_injection6(fault_injection_list[3511:], ser, "b12_retry_Comp0_0_100us_3511.txt")
    # start_fault_injection6(fault_injection_list[3821:], ser, "b12_retry_Comp0_0_100us_3821.txt")
    # start_fault_injection6(fault_injection_list, ser, "b12_retry_Comp0_0_10us.txt")
    # start_fault_injection6(fault_injection_list[1838:], ser, "b12_retry_Comp0_0_10us_1838.txt")
    # start_fault_injection6(fault_injection_list[3506:], ser, "b12_retry_Comp0_0_10us_3506.txt")
    # start_fault_injection6(fault_injection_list[3511:], ser, "b12_retry_Comp0_0_10us_3511.txt")
    # start_fault_injection6(fault_injection_list[1838:], ser, "b12_retry_Comp0_0_2us_1838.txt")
    # start_fault_injection6(fault_injection_list[3506:], ser, "b12_retry_Comp0_0_2us_3506.txt")
    # start_fault_injection6(fault_injection_list[3511:], ser, "b12_retry_Comp0_0_2us_3511.txt")
    # start_fault_injection6(fault_injection_list[3821:], ser, "b12_retry_Comp0_0_10us_3821.txt")

    # while True:
    #     command = input("Type something to send or 'R' to receive or 'X' to quit: ")
    #     serial_command(ser, command)


def main_compare_EBDs():
    # open file
    inp = get_input_parameters("input")
    print(inp)
    list_of_lines_with_essentialbits, radix_name = read_lines_with_essentialbits_from_list_of_files(inp)
    print(list_of_lines_with_essentialbits)

    for num in range(len(list_of_lines_with_essentialbits)-1):
        list_to_sub1 = [list_of_lines_with_essentialbits[num+1], list_of_lines_with_essentialbits[0]]

        diff1 = compare_two_list_and_return_different_EBs(list_to_sub1)
        print(diff1)

        write_list_of_tuple_to_file("EBs_only_at_" + radix_name[num+1] + ".txt", diff1)


if __name__ == '__main__':
    main_serial()
    # main_compare_EBDs()
