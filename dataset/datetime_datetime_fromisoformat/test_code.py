    def test_fromisoformat_datetime(self):
        # Test that isoformat() is reversible
        base_dates = [
            (1, 1, 1),
            (1900, 1, 1),
            (2004, 11, 12),
            (2017, 5, 30)
        ]

        base_times = [
            (0, 0, 0, 0),
            (0, 0, 0, 241000),
            (0, 0, 0, 234567),
            (12, 30, 45, 234567)
        ]

        separators = [' ', 'T']

        tzinfos = [None, timezone.utc,
                   timezone(timedelta(hours=-5)),
                   timezone(timedelta(hours=2))]

        dts = [datetime(*date_tuple, *time_tuple, tzinfo=tzi)
               for date_tuple in base_dates
               for time_tuple in base_times
               for tzi in tzinfos]

        for dt in dts:
            for sep in separators:
                dtstr = dt.isoformat(sep=sep)

                with self.subTest(dtstr=dtstr):
                    dt_rt = datetime.fromisoformat(dtstr)
                    self.assertEqual(dt, dt_rt)

    def test_fromisoformat_timezone(self):
        base_dt = datetime(2014, 12, 30, 12, 30, 45, 217456)

        tzoffsets = [
            timedelta(hours=5), timedelta(hours=2),
            timedelta(hours=6, minutes=27),
            timedelta(hours=12, minutes=32, seconds=30),
            timedelta(hours=2, minutes=4, seconds=9, microseconds=123456)
        ]

        tzoffsets += [-1 * td for td in tzoffsets]

        tzinfos = [None, timezone.utc,
                   timezone(timedelta(hours=0))]

        tzinfos += [timezone(td) for td in tzoffsets]

        for tzi in tzinfos:
            dt = base_dt.replace(tzinfo=tzi)
            dtstr = dt.isoformat()

            with self.subTest(tstr=dtstr):
                dt_rt = datetime.fromisoformat(dtstr)
                assert dt == dt_rt, dt_rt

    def test_fromisoformat_separators(self):
        separators = [
            ' ', 'T', '\u007f',     # 1-bit widths
            '\u0080', 'ʁ',          # 2-bit widths
            'ᛇ', '時',               # 3-bit widths
            '🐍',                    # 4-bit widths
            '\ud800',               # bpo-34454: Surrogate code point
        ]

        for sep in separators:
            dt = datetime(2018, 1, 31, 23, 59, 47, 124789)
            dtstr = dt.isoformat(sep=sep)

            with self.subTest(dtstr=dtstr):
                dt_rt = datetime.fromisoformat(dtstr)
                self.assertEqual(dt, dt_rt)

    def test_fromisoformat_ambiguous(self):
        # Test strings like 2018-01-31+12:15 (where +12:15 is not a time zone)
        separators = ['+', '-']
        for sep in separators:
            dt = datetime(2018, 1, 31, 12, 15)
            dtstr = dt.isoformat(sep=sep)

            with self.subTest(dtstr=dtstr):
                dt_rt = datetime.fromisoformat(dtstr)
                self.assertEqual(dt, dt_rt)

    def test_fromisoformat_timespecs(self):
        datetime_bases = [
            (2009, 12, 4, 8, 17, 45, 123456),
            (2009, 12, 4, 8, 17, 45, 0)]

        tzinfos = [None, timezone.utc,
                   timezone(timedelta(hours=-5)),
                   timezone(timedelta(hours=2)),
                   timezone(timedelta(hours=6, minutes=27))]

        timespecs = ['hours', 'minutes', 'seconds',
                     'milliseconds', 'microseconds']

        for ip, ts in enumerate(timespecs):
            for tzi in tzinfos:
                for dt_tuple in datetime_bases:
                    if ts == 'milliseconds':
                        new_microseconds = 1000 * (dt_tuple[6] // 1000)
                        dt_tuple = dt_tuple[0:6] + (new_microseconds,)

                    dt = datetime(*(dt_tuple[0:(4 + ip)]), tzinfo=tzi)
                    dtstr = dt.isoformat(timespec=ts)
                    with self.subTest(dtstr=dtstr):
                        dt_rt = datetime.fromisoformat(dtstr)
                        self.assertEqual(dt, dt_rt)

    def test_fromisoformat_fails_datetime(self):
        # Test that fromisoformat() fails on invalid values
        bad_strs = [
            '',                             # Empty string
            '\ud800',                       # bpo-34454: Surrogate code point
            '2009.04-19T03',                # Wrong first separator
            '2009-04.19T03',                # Wrong second separator
            '2009-04-19T0a',                # Invalid hours
            '2009-04-19T03:1a:45',          # Invalid minutes
            '2009-04-19T03:15:4a',          # Invalid seconds
            '2009-04-19T03;15:45',          # Bad first time separator
            '2009-04-19T03:15;45',          # Bad second time separator
            '2009-04-19T03:15:4500:00',     # Bad time zone separator
            '2009-04-19T03:15:45.2345',     # Too many digits for milliseconds
            '2009-04-19T03:15:45.1234567',  # Too many digits for microseconds
            '2009-04-19T03:15:45.123456+24:30',    # Invalid time zone offset
            '2009-04-19T03:15:45.123456-24:30',    # Invalid negative offset
            '2009-04-10ᛇᛇᛇᛇᛇ12:15',         # Too many unicode separators
            '2009-04\ud80010T12:15',        # Surrogate char in date
            '2009-04-10T12\ud80015',        # Surrogate char in time
            '2009-04-19T1',                 # Incomplete hours
            '2009-04-19T12:3',              # Incomplete minutes
            '2009-04-19T12:30:4',           # Incomplete seconds
            '2009-04-19T12:',               # Ends with time separator
            '2009-04-19T12:30:',            # Ends with time separator
            '2009-04-19T12:30:45.',         # Ends with time separator
            '2009-04-19T12:30:45.123456+',  # Ends with timzone separator
            '2009-04-19T12:30:45.123456-',  # Ends with timzone separator
            '2009-04-19T12:30:45.123456-05:00a',    # Extra text
            '2009-04-19T12:30:45.123-05:00a',       # Extra text
            '2009-04-19T12:30:45-05:00a',           # Extra text
        ]

        for bad_str in bad_strs:
            with self.subTest(bad_str=bad_str):
                with self.assertRaises(ValueError):
                    datetime.fromisoformat(bad_str)

    def test_fromisoformat_fails_surrogate(self):
        # Test that when fromisoformat() fails with a surrogate character as
        # the separator, the error message contains the original string
        dtstr = "2018-01-03\ud80001:0113"

        with self.assertRaisesRegex(ValueError, re.escape(repr(dtstr))):
            datetime.fromisoformat(dtstr)

    def test_fromisoformat_utc(self):
        dt_str = '2014-04-19T13:21:13+00:00'
        dt = datetime.fromisoformat(dt_str)

        self.assertIs(dt.tzinfo, timezone.utc)