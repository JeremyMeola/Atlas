import pyb

PMTK_SET_NMEA_UPDATE_100_MILLIHERTZ = "$PMTK220,10000*2F"
PMTK_SET_NMEA_UPDATE_200_MILLIHERTZ = "$PMTK220,5000*1B"  # Once every 5 seconds, 200 millihertz.
PMTK_SET_NMEA_UPDATE_1HZ = "$PMTK220,1000*1F"
PMTK_SET_NMEA_UPDATE_5HZ = "$PMTK220,200*2C"
PMTK_SET_NMEA_UPDATE_10HZ = "$PMTK220,100*2F"
# Position fix update rate commands.
PMTK_API_SET_FIX_CTL_100_MILLIHERTZ = "$PMTK300,10000,0,0,0,0*2C"  # Once every 10 seconds, 100 millihertz.
PMTK_API_SET_FIX_CTL_200_MILLIHERTZ = "$PMTK300,5000,0,0,0,0*18"  # Once every 5 seconds, 200 millihertz.
PMTK_API_SET_FIX_CTL_1HZ = "$PMTK300,1000,0,0,0,0*1C"
PMTK_API_SET_FIX_CTL_5HZ = "$PMTK300,200,0,0,0,0*2F"
# Can't fix position faster than 5 times a second!


PMTK_SET_BAUD_57600 = "$PMTK251,57600*2C"
PMTK_SET_BAUD_9600 = "$PMTK251,9600*17"

# turn on only the second sentence (GPRMC)
PMTK_SET_NMEA_OUTPUT_RMCONLY = "$PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29"
# turn on GPRMC and GGA
PMTK_SET_NMEA_OUTPUT_RMCGGA = "$PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*28"
# turn on ALL THE DATA
PMTK_SET_NMEA_OUTPUT_ALLDATA = "$PMTK314,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0*28"
# turn off output
PMTK_SET_NMEA_OUTPUT_OFF = "$PMTK314,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*28"

# to generate your own sentences, check out the MTK command datasheet and use a checksum calculator
# such as the awesome http:#www.hhhh.org/wiml/proj/nmeaxor.html

PMTK_LOCUS_STARTLOG = "$PMTK185,0*22"
PMTK_LOCUS_STOPLOG = "$PMTK185,1*23"
PMTK_LOCUS_STARTSTOPACK = "$PMTK001,185,3*3C"
PMTK_LOCUS_QUERY_STATUS = "$PMTK183*38"
PMTK_LOCUS_ERASE_FLASH = "$PMTK184,1*22"
LOCUS_OVERLAP = 0
LOCUS_FULLSTOP = 1

PMTK_ENABLE_SBAS = "$PMTK313,1*2E"
PMTK_ENABLE_WAAS = "$PMTK301,2*2E"

# standby command & boot successful message
PMTK_STANDBY = "$PMTK161,0*28"
PMTK_STANDBY_SUCCESS = "$PMTK001,161,3*36"  # Not needed currently
PMTK_AWAKE = "$PMTK010,002*2D"

# ask for the release and version
PMTK_Q_RELEASE = "$PMTK605*31"

# request for updates on antenna status
PGCMD_ANTENNA = "$PGCMD,33,1*6C"
PGCMD_NOANTENNA = "$PGCMD,33,0*6D"

# how long to wait when we're looking for a response
MAXWAITSENTENCE = 5
MAXLINELENGTH = 120


class AdafruitGPS:
    def __init__(self, uart_bus, timer_num, baud_rate, update_rate):
        self.hour = 0
        self.minute = 0
        self.seconds = 0

        self.day = 0
        self.month = 0
        self.year = 0

        self.latitude_deg = 0
        self.latitude_min = 0.0
        self.latitude = 0.0
        self.lat_direction = 'N'

        self.longitude_deg = 0
        self.longitude_min = 0.0
        self.longitude = 0.0
        self.long_direction = 'W'

        self.num_satellites = 0
        self.hdop = 0.0

        self.altitude = 0.0
        self.geoid_height = 0.0

        self.fix = False

        self.speed_knots = 0.0

        self.magnetic_variation = 0.0
        self.mag_var_direction = 'W'

        self.paused = False

        self.current_line = b''
        self.previous_line = b''
        self.recved_flag = True

        self.in_standby_mode = False

        self.init_uart(uart_bus, baud_rate, update_rate)
        self.timer = pyb.Timer(timer_num, freq=1000)  # call every 1 ms
        self.timer.callback(lambda t: self.timer_callback())

    def init_uart(self, uart_bus, baud_rate, update_rate):
        self.uart = pyb.UART(uart_bus, baud_rate, read_buf_len=1000)

        pyb.delay(50)

        # get RMC and GGA sentences at 1 hz
        if update_rate == 1:
            self.send_command(PMTK_SET_NMEA_OUTPUT_RMCGGA)
            self.send_command(PMTK_SET_NMEA_UPDATE_1HZ)
            self.send_command(PMTK_API_SET_FIX_CTL_1HZ)
        elif update_rate == 5:
            # get RMC and GGA sentences at 5 hz
            self.send_command(PMTK_SET_NMEA_OUTPUT_RMCGGA)
            self.send_command(PMTK_SET_NMEA_UPDATE_5HZ)
            self.send_command(PMTK_API_SET_FIX_CTL_5HZ)
        elif update_rate == 10:
            if baud_rate == 9600:  # send less data if using slower baud rate
                self.send_command(PMTK_SET_NMEA_OUTPUT_RMCONLY)
            elif baud_rate == 57600:
                self.send_command(PMTK_SET_NMEA_OUTPUT_RMCGGA)
            else:
                raise ValueError("Invalid baud rate:", baud_rate)

            self.send_command(PMTK_SET_NMEA_UPDATE_10HZ)
            # fix can't update at 10 hz
            self.send_command(PMTK_API_SET_FIX_CTL_5HZ)
        else:
            raise ValueError("Invalid update rate:", update_rate)

    def timer_callback(self):
        self.read()

    def parse(self, sentence):
        # do checksum, first look if we have one
        if sentence[-3] == b'*':
            sum = self.parse_hex(sentence[-2]) * 16
            sum += self.parse_hex(sentence[-1])

            # check checksum
            for index in range(1, len(sentence) - 3):
                sum ^= ord(sentence[index])

            if sum != 0:
                # bad checksum :(
                return False

        if "$GPGGA" in sentence:
            self.parse_gga_sentence(sentence)
        elif "GPRMC":
            self.parse_rmc_sentence(sentence)

    def parse_gga_sentence(self, sentence):
        """
        example:
        $GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47

        GGA          Global Positioning System Fix Data
        123519       Fix taken at 12:35:19 UTC
        4807.038,N   Latitude 48 deg 07.038' N
        01131.000,E  Longitude 11 deg 31.000' E
        1            Fix quality: 0 = invalid
                                  1 = GPS fix (SPS)
                                  2 = DGPS fix
                                  3 = PPS fix
                                  4 = Real Time Kinematic
                                  5 = Float RTK
                                  6 = estimated (dead reckoning) (2.3 feature)
                                  7 = Manual input mode
                                  8 = Simulation mode
        08           Number of satellites being tracked
        0.9          Horizontal dilution of position
        545.4,M      Altitude, Meters, above mean sea level
        46.9,M       Height of geoid (mean sea level) above WGS84
                         ellipsoid
        (empty field) time in seconds since last DGPS update
        (empty field) DGPS station ID number
        *47          the checksum data, always begins with *

        see http://www.gpsinformation.org/dale/nmea.htm#GGA for more
        """
        _, time, latitude, lat_direction, longitude, long_direction, \
        fix_quality, num_satellites, hdop, altitude, altitude_units, \
        geoid_height, geoid_height_units, _, _, checksum = \
            sentence.split(",")

        self.parse_time(time)

        self.parse_latitude(latitude, lat_direction)
        self.parse_longitude(longitude, long_direction)

        self.num_satellites = int(num_satellites)
        self.hdop = float(hdop)

        self.altitude = float(altitude)
        self.geoid_height = float(geoid_height)

    def parse_rmc_sentence(self, sentence):
        """
        example:
        $GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A

         RMC          Recommended Minimum sentence C
         123519       Fix taken at 12:35:19 UTC
         A            Status A=active or V=Void.
         4807.038,N   Latitude 48 deg 07.038' N
         01131.000,E  Longitude 11 deg 31.000' E
         022.4        Speed over the ground in knots
         084.4        Track angle in degrees True
         230394       Date - 23rd of March 1994
         003.1,W      Magnetic Variation
         *6A          The checksum data, always begins with *
        """

        _, time, fix_status, latitude, lat_direction, longitude, \
        long_direction, speed_knots, bearing, date, mag_variation, \
        mag_direction, checksum = sentence.split(",")

        self.parse_time(time)

        self.fix = True if fix_status == "A" else False

        self.parse_latitude(latitude, lat_direction)
        self.parse_longitude(longitude, long_direction)

        self.speed_knots = float(speed_knots)

        self.parse_date(date)

        self.magnetic_variation = float(mag_variation)
        self.mag_var_direction = mag_direction.decode('ascii')

    def parse_date(self, date_sentence):
        self.day = int(date_sentence[0:2])
        self.month = int(date_sentence[2:4])
        self.year = int(date_sentence[4:6])

    def parse_time(self, time_sentence):
        self.hour = int(time_sentence[0:2])
        self.minute = int(time_sentence[2:4])
        self.seconds = int(time_sentence[4:6])

    def parse_latitude(self, latitude, lat_direction):
        self.latitude_deg = int(latitude[0:2])
        self.latitude_min = float(latitude[2:])
        self.latitude = self.latitude_deg + self.latitude_min / 60
        self.lat_direction = lat_direction.decode('ascii')
        if self.lat_direction != "N":  # switch south to north
            self.latitude *= -1

    def parse_longitude(self, longitude, long_direction):
        self.longitude_deg = int(longitude[0:2])
        self.longitude_min = float(longitude[2:])
        self.longitude = self.longitude_deg + self.longitude_min / 60
        self.long_direction = long_direction.decode('ascii')
        if self.long_direction != "W":  # switch east to west
            self.longitude *= -1

    @staticmethod
    def parse_hex(byte_char):
        # convert hex byte to int
        return int(byte_char, 16)

    def read(self):
        if self.paused: return

        if self.uart.any():
            char = self.uart.read()
        else:
            return

        if char == b'\n':
            self.previous_line = self.current_line
            self.current_line = b''
            self.recved_flag = True
        else:
            self.current_line += char

    def received_sentence(self):
        if self.recved_flag is True:
            self.recved_flag = False
            self.parse(self.previous_line)
            return True
        else:
            return False

    def wait_for_sentence(self, sentence, max_wait_count=5):
        counter = 0
        while counter < max_wait_count:
            if self.received_sentence():
                # current_line is modified constantly. previous_line is the
                # last complete sentence
                if sentence == self.previous_line:
                    return True
                counter += 1
        return False

    def standby(self):
        if self.in_standby_mode:  # do nothing if in standby already
            return False
        else:
            self.in_standby_mode = True
            self.send_command(PMTK_STANDBY)
            return True

    def wakeup(self):
        if self.in_standby_mode:
            self.in_standby_mode = True
            self.send_command("")  # send byte to wake it up
            return self.wait_for_sentence(PMTK_AWAKE)
        else:
            return False

    def send_command(self, command):  # command is a string
        self.uart.write(command.encode('ascii') + b'\n')
