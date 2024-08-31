    def test_isocalendar(self):
        week_mondays = [
                ((2003, 12, 22), (2003, 52, 1)),
                ((2003, 12, 29), (2004, 1, 1)),
                ((2004, 1, 5), (2004, 2, 1)),
                ((2009, 12, 21), (2009, 52, 1)),
                ((2009, 12, 28), (2009, 53, 1)),
                ((2010, 1, 4), (2010, 1, 1)),
        ]

        test_cases = []
        for cal_date, iso_date in week_mondays:
            base_date = date(*cal_date)
            for i in range(7):
                new_date = base_date + timedelta(i)
                new_iso = iso_date[0:2] + (iso_date[2] + i,)
                test_cases.append((new_date, new_iso))

        for d, exp_iso in test_cases:
            with self.subTest(d=d, comparison="tuple"):
                self.assertEqual(d.isocalendar(), exp_iso)

            with self.subTest(d=d, comparison="fields"):
                t = d.isocalendar()
                self.assertEqual((t.year, t.week, t.weekday), exp_iso)

    def test_iso_long_years(self):
        ISO_LONG_YEARS_TABLE = """
              4   32   60   88
              9   37   65   93
             15   43   71   99
             20   48   76
             26   54   82

            105  133  161  189
            111  139  167  195
            116  144  172
            122  150  178
            128  156  184

            201  229  257  285
            207  235  263  291
            212  240  268  296
            218  246  274
            224  252  280

            303  331  359  387
            308  336  364  392
            314  342  370  398
            320  348  376
            325  353  381
        """
        iso_long_years = sorted(map(int, ISO_LONG_YEARS_TABLE.split()))
        L = []
        for i in range(400):
            d = date(2000+i, 12, 31)
            d1 = date(1600+i, 12, 31)
            self.assertEqual(d.isocalendar()[1:], d1.isocalendar()[1:])
            if d.isocalendar()[1] == 53:
                L.append(i)
        self.assertEqual(L, iso_long_years)
