import socket
import threading
import alphabets
import datetime
import time

__author__ = 'Eduardo J Castillo'
__email__ = 'castilloej@email.wofford.edu'


class Bridge:

    """
    This object class represents a bridge, that is, one of the ways through which part of the message
    is going to be transmitted. Using objects for this matter represents abstraction in the implementation
    which later allows us to add or remove bridges more easily from the covert implementation
    """

    def __init__(self, ip, port, alphabet):

        """
        Constructor
        :param ip: IP of the Bridge corresponding to this object
        :param port: Port being listened on the Bridge
        :param alphabet: Alphabet of the encoding expected by the receiver
        :return:
        """

        self._ip = ip
        self._port = port
        self._alphabet = alphabet
        self._message = ''
        self._started = datetime.datetime.now()

    def _send_packet(self):

        """
        All this function does is send a packet right when it is executed
        :return:
        """

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        s.connect((self._ip, self._port))
        s.send(bytes('-', 'UTF-8'))
        s.close()

    def _send_sequence(self, sequence):

        """
        This function makes sure to wait for every interval in a sequence that represents, for example,
        the watermark of a letter, or the final message signal. The sequences are represented in lists.
        Note that in this function a "10" is automatically added to the list, this 10 is used for delay
        probability calculation.

        :param sequence: list that contains numbers that represent water intervals
        :return:
        """

        for waittime in sequence + [10]:

            # The sleep function only accepts info in seconds, not microseconds as we are interested
            # so we must divide by one hundred. Note that since each object is being ran in a different thread
            # the sleep() function does not affect other bridges and only the one being ran
            time.sleep(waittime / 100)
            self._send_packet()

    def _start_covert(self):

        """
        This function signals the initiation of a covert message by sending the sequence that matches the starter function
        :return:
        """

        print('Starting to send message to IP:', self._ip, 'on PORT:', self._port)

        self._send_sequence([0] + self._alphabet['starter'])

    def _end_covert(self):

        """
        This function signals the end of a covert message through this bridge by waiting four seconds and sending a packet
        :return:
        """

        self._send_sequence([400])
        print('The message ENDED through the IP:', self._ip, 'on PORT', self._port, (datetime.datetime.now() - self._started))

    def getIP(self):

        """
        Accesor function to get the IP of the Bridge
        :return: IP of the bridge
        """

        return self._ip

    def getPort(self):

        """
        Accesor function to get the port of the Bridge
        :return:
        """
        return str(self._port)

    def send_message(self):

        """
        This function starts the covert message and then sends the sequence for every character part of the string
        that was assigned to this bridge, and then it signals the end of covert.
        :return:
        """

        if self._message:

            self._start_covert()

            for letter in self._message:

                self._send_sequence(self._alphabet[letter])

            self._end_covert()

    def add(self, string):

        """
        This function adds characters to the current string to be sent through this bridge. All letters are turned
        into uppercase given that the letters are only in uppercase in the alphabet.
        :param string: String to be added to the containing list in the object to be sent over this bridge
        :return:
        """
        self._message += string.upper()


def activate_bridge(bridge):

    """
    This is a helper used to start the execution of bridges on different threads.
    NOTE: MIGHT BE DELETED AFTER SOME CODE OPTIMIZATION
    :param bridge: Object of the class Bridge
    :return:
    """
    try:
        bridge.send_message()
    except ConnectionRefusedError:
        print('ERROR', bridge.getIP(), 'at', bridge.getPort() + ':', 'Either the bridge and/or final receiver is down')


def main():

    # Edit the following variable to add or remove bridges to send your message

    # List that contains the bridges to be used for this implementation. See the parameters of the class for reference
    Bridges = [Bridge('201.211.236.187', 50003, alphabets.alphabet_one)]

    # Stop editing here !

    complete_message = input('Please provide the message to send: ')
    print()

    current_br = 0

    # We need to assign a string to each of the bridges we created, so we execute the following code
    # to split the message provided correctly
    for bridge in Bridges:

        bridge.add(complete_message[current_br::len(Bridges)])
        current_br += 1

    # Now we activate every bridges on a different thread by using the helper function
    for bridge in Bridges:

        threading.Thread(target=activate_bridge, args=(bridge,)).start()

main()
