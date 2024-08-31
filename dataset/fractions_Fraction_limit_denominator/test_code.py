F = fractions.Fraction

    def testLimitDenominator(self):
        rpi = F('3.1415926535897932')
        self.assertEqual(rpi.limit_denominator(10000), F(355, 113))
        self.assertEqual(-rpi.limit_denominator(10000), F(-355, 113))
        self.assertEqual(rpi.limit_denominator(113), F(355, 113))
        self.assertEqual(rpi.limit_denominator(112), F(333, 106))
        self.assertEqual(F(201, 200).limit_denominator(100), F(1))
        self.assertEqual(F(201, 200).limit_denominator(101), F(102, 101))
        self.assertEqual(F(0).limit_denominator(10000), F(0))
        for i in (0, -1):
            self.assertRaisesMessage(
                ValueError, "max_denominator should be at least 1",
                F(1).limit_denominator, i)