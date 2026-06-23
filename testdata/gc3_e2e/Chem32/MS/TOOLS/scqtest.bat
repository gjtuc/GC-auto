echo off
set scaddr=0		 >scqtest.txt
set scchan=lan[%1]:hpib >>scqtest.txt
scq "*idn?"		>>scqtest.txt
