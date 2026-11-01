import unittest
import pandas as pd
from analyze import analyze

class Tests(unittest.TestCase):
    def setUp(self):
        self.d=pd.DataFrame({'Customer_ID':[1,2,3,4],'Churn':[1,0,1,0],'Complains':[1,0,None,0], 'Tariff_Plan':[1,1,2,2],'Charge_Amount':[0,0,1,1]})
    def test_counts_and_missing_category(self):
        t,s=analyze(self.d);self.assertEqual(s['churn_rate'],.5)
        for _,g in t.groupby('segment'):
            self.assertEqual(g.customers.sum(),4);self.assertEqual(g.churned.sum(),2)
        row=t[(t.segment=='Complains') & (t.code=='Missing')].iloc[0]
        self.assertEqual(row.churn_rate,1)
    def test_wilson_known_interval(self):
        t,_=analyze(self.d);r=t[(t.segment=='Tariff_Plan') & (t.code=='1')].iloc[0]
        self.assertAlmostEqual(r.lower_95,.0945312057342307)
        self.assertAlmostEqual(r.upper_95,.9054687942657693)
    def test_duplicate_id(self):
        self.d.loc[1,'Customer_ID']=1
        with self.assertRaises(ValueError): analyze(self.d)
    def test_invalid_codes(self):
        for col in ['Churn','Complains','Tariff_Plan','Charge_Amount']:
            d=self.d.copy();d.loc[0,col]=99
            with self.assertRaises(ValueError): analyze(d)
    def test_missing_target_and_id(self):
        for col in ['Churn','Customer_ID']:
            d=self.d.copy();d.loc[0,col]=None
            with self.assertRaises(ValueError): analyze(d)
    def test_empty_and_schema(self):
        for d in [self.d.iloc[:0],self.d.drop(columns='Churn')]:
            with self.assertRaises(ValueError): analyze(d)
if __name__=='__main__': unittest.main()
