import socket
import alphabets
import threading
import datetime
import time

__author__ = 'Eduardo J Castillo'
__email__ = 'castilloej@email.wofford.edu'


class ListenMessage:

    def __init__(self, alphabet, port, ip=''):

        """

        :param alphabet: Alphabet expected to be used for the encoding of the message to be able to decode
        :param port: Port to listen to on this bridge
        :param ip: IP to listen to. Note: You may live this input empty
        :return:
        """
        self._ip = ip
        self._port = port
        self._alphabet = alphabet
        self._started = False
        self._finished = False
        self._forcequit = False
        self._lastarrival = None
        self._message = ''
        self._current_sequence = []

    def _DecodeSequence(self, sequence):

        """
        This function receives a sequence with the times that were received through this bridges and tries to
        find a match, and it returns the most likely character. To make sure this function which is process
        heavy in comaparison to others, and the sensitivity of time in this implementation, this function is
        executed on a different thread to avoid messing up the reception of packets at the correct tine
        :param sequence: List containing time intervals in microseconds
        :return:
        """

        # This two variables will contain both the most likely character at a given time, and then the delay
        # total among all its values compared to what is on the alphabet. The member of the alphabet that ends
        # up having the lowest number on the delay difference from the alphabet is the most likely to be the one sent
        possible_value = ''
        possible_index = 9999999

        # We estimate the delay of the transmission by comparing what we received as last member of the sequence
        # which should be the hardcoded 10. Then we pop-ip. (Since it's the last member of the list, the pop is O(1))
        delay = sequence[5] - 10
        sequence.pop(5)

        # We go through every member in the alphabet and compare the intervals we received with the ones in each member
        # of the alphabet to calculate the total delays for that alphabet member, then if the total delay for that given
        # sequence is less than what we were storing, we replace it
        for some_sequence in self._alphabet:

            total_differ = 0
            current_index = 0

            for delayX in self._alphabet[some_sequence]:
                # We square the difference and then we square root it so all the differences are converted in positive numbers
                total_differ += ((delayX - sequence[current_index] + delay)**2)**(1/2)
                current_index += 1

            if total_differ < possible_index:
                possible_index = total_differ
                possible_value = some_sequence

        # DEBUG HERE - TO CHECK TIMINGS OF SEQUENCES AS THEY ARRIVE AND THE LIKELY CHARACTER
        print(sequence, possible_value, self._ip, self._port, delay)

        return possible_value

    def add_to_message(self, sequence):

        """
        This is used to add the most likely letter of the received sequence to the final message that is being
        stored for this bridge
        :param sequence: Sequence (list) of received time intervals
        :return:
        """

        self._message += self._DecodeSequence(sequence)

    def _finish(self):

        """
        Used to indicate the message finished being transmitted.
        :return:
        """

        self._finished = True

    def GetMessage(self):

        """
        Accessor function to get the current/final message
        :return:
        """

        return self._message

    def ForceQuit(self):

        """
        This function is intended to force the termination of listening to a message
        it is currently not used, but was implemented for probable future uses!
        :return:
        """

        self._forcequit = True

    def Finished(self):

        """
        This returns a boolean value that signifies whether the final signal was sent or not
        :return:
        """

        return self._finished

    def StartListening(self):

        """
        This function is perhaps the most crucial one because it is the one that receives the packets
        and processes them as they arrive by keeping track of these correctly.
        :return:
        """

        print('Waiting for a covert message from', self._ip, 'on PORT', self._port)

        backlog = 5
        size = 100
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self._ip, self._port))
        s.listen(backlog)

        # The program will listen on the provdided port and if provided, IP
        while not self._finished or not self._forcequit:

            # We accept the packet
            client, address = s.accept()
            data = client.recv(size)

            if data:

                # In the case that the last arrival is set to None, means this is the first packet and the interval
                # is useless, because it represents the interval since this script started to be ran and now. Not a real
                # interval sent by the sender.
                if self._lastarrival:

                    # Since the interval is valid, we calculate what it is comparing the current time to the time of the
                    # previous packet
                    current_time = datetime.datetime.now()
                    difference = current_time - self._lastarrival

                    second_difference = difference.seconds
                    micros_difference = difference.microseconds / 10000

                    # If the time difference is equal of more than 3, and the covert had been started that means the end
                    # signal was sent
                    if self._started and second_difference >= 3:
                        self._finish()
                    # Given that it was not the end signal, it was just another time interval
                    else:
                        self._current_sequence.append(micros_difference)

                    # In the case that there are now six members of current sequence, it means it is complete.
                    # Five members represent time intervals, and the sixth is the hardcoded ten to predict delays
                    if len(self._current_sequence) == 6:

                        # If the starter signal was not sent, we check if the sequence matches with the starter
                        # if it does not, since the starter signal has not been sent, then the sequence is discarded
                        if not self._started and self._DecodeSequence(self._current_sequence) == 'starter':
                            self._started = True
                            print('Covert communication started!')
                        elif self._started:
                            # if the starter signal had been sent, then a new thread is started to decode the
                            # sequence we received. We do this to avoid processing hinder the reception of other packets
                            threading.Thread(target=self.add_to_message, args=(self._current_sequence,)).start()

                        # We empty the current sequence to receive the next one
                        self._current_sequence = []

                self._lastarrival = datetime.datetime.now()


class MessageReceptionManager:

    def __init__(self):

        self._br_num = 0
        self._br_don = 0
        self._status = ['IDLE']
        self._bridges = []
        self._final_m = []

    def AddBridge(self, alphabet, port, ip=''):

        """
        We use this to add bridges to this covert channel
        :param alphabet: The alphabet to be used through this bridge
        :param port: The port to listen to through this bridge
        :param ip: The IP to listen to in this bridge. (Not requiered)
        :return:
        """
        self._br_num += 1
        self._bridges.append(ListenMessage(alphabet, port, ip))

    def StartListening(self):

        """
        Initiates the listening in every bridge
        :return:
        """

        # The status variable is used for debugging purposes only
        self._status.append('STARTING')

        current_br = 0

        # We go through every bridge and start it in different threads so they do not affect each other
        for bridge in self._bridges:

            threading.Thread(target=bridge.StartListening).start()

            # We use the bridge_status_polling so we know when all the bridges end to rebuild the message
            threading.Thread(target=self._bridge_status_polling, args=(bridge,)).start()
            self._status.append('BRIDGE ' + str(current_br) + ' STARTED')
            current_br += 1

    def FinishedCovert(self):

        """
        This function is executed when all the bridges have finished receiving the message so it is reconstructed
        :return:
        """
        print('All bridges finished!')

        msg_len = 0

        # We calculate the total length of the message to allocate a list this long
        for Bridge in self._bridges:

            msg_len += len(Bridge.GetMessage())

        # We allocate a list containing long enough to fit all the characters from all the bridges
        # so we can rebuild the message
        self._final_m = [None]*msg_len

        current_br = 0

        # We go through every bridge and add the messages to the list we created on their rightful spots
        for Bridge in self._bridges:

            current_index = current_br

            for character in Bridge.GetMessage():
                self._final_m[current_index] = character
                current_index += self._br_num

            current_br += 1

        # We print the final result
        print('\nThe message is: ' + ''.join(self._final_m))

    def _bridge_status_polling(self, bridge):

        """
        We use this function to check the status of the provided bridge to signal when it finished
        whenever all the bridges have finished receiving the message we execute the FinishedCovert()
        to reconstruct the final message
        :param bridge: Bridge to listen to
        :return:
        """

        while True:

            if not bridge.Finished():

                # Since we do not want to waste resources unnecessarily, if the bridge has not finished
                # we let this undefined loop to sleep for one second before checking the status again.
                time.sleep(1)

            else:

                self._br_don += 1

                if self._br_don == self._br_num:
                    self.FinishedCovert()

                break


def main():

    CovertChannel = MessageReceptionManager()

    CovertChannel.AddBridge(alphabets.alphabet_one, 50003)
    #CovertChannel.AddBridge(alphabets.alphabet_one, 50004)
    #CovertChannel.AddBridge(alphabets.alphabet_one, 50005)

    CovertChannel.StartListening()






main()






