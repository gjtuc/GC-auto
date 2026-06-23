rem  
rem
ipconfig /all			 >ipconfig.txt
net start			>>ipconfig.txt
net config workstation		>>ipconfig.txt
net config server		>>ipconfig.txt
net statistics workstation	>>ipconfig.txt
rem nslookup set all		>>ipconfig.txt
rem