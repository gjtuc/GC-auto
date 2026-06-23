rem Pingtest.txt should contain something similar to the next four lines.
rem 
rem Pinging 15.25.205.117 with 32 bytes of data:
rem 
rem Reply from 15.25.205.117: bytes=32 time<10ms TTL=60
rem---------------------------------------------------
echo off
ping -w 5000 -n 1 %1 >pingtest.txt