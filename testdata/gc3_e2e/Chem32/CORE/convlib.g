! Macro to convert Pascal library files (*.L) to a macro file (*.PLF)
! for the DOS 3D-chemstation to generate new library file (*.UVL)
!
! ConvLib [Library file]
!
Name ConvLib
 PARAMETER file$ default "?"
 LOCAL nentries,i,j,x,y,npnts,a1$,newfile$,mess1$
 
 DAD file,file$
 mess "                                                                ",,0,-1
 mess "                                                                ",,0,-2
 nentries=nobjects
 strpos ".",file_l$
 i=value
 strpos ":",file_l$
 conv file$,file_l$[value+1:i-1]
 conv path$,file_l$[1:value]
 conv newfile$,file$,".UVL"
 strpos "",file$
 if len2>5
  conv file$,file$[1:5]
  conv mess1$,"File name to long, "
 else
  conv mess1$,""
 endif
 conv ofile$,path$,file$,".PLF"
 conv mess1$,mess1$,ofile$
 mess mess1$,,0,-1
 fclose 
 fopen ofile$,output
  writeln 1,"#34"
  fclose 1
  fopen ofile$,input
  readln 2,q$
  fclose 2
 fopen ofile$,output

 ! start writing the data
 
 ! write a identification string
 writeln 1,"! Pascal-Dos Spectral library converion macro Vers. 1.01"

 writeln 1,""
 writeln 1,"Name StartLibConversion"
 writeln 1," LibFile$=",q$,file_l$,q$
 writeln 1," LibOperator$=",q$,operator$,q$
 writeln 1," LibDateTime$=",q$,cr_date$,q$
 writeln 1,""
 writeln 1," If Check( macro, MakeNewConvLibrary ) <> 1"
 writeln 1,"   Macro ",q$,"ConvLib.mac",q$
 writeln 1," endif"
 writeln 1,"" 
 writeln 1," MakeNewConvLibrary ",q$, newfile$,   q$,", #92"
 writeln 1,"                    ",q$, lib_name$,  q$,", #92"
 writeln 1,"                    ",q$, Operator$,  q$,", #92"
 writeln 1,"                    ",q$, cr_date$,   q$,", #92"
 writeln 1,"                    ",q$, lib_info1$, q$,", #92"
 writeln 1,"                    ",q$, lib_info2$, q$,", #92"
 writeln 1,"                    ",q$, lib_info3$, q$,", #92"
 writeln 1,"                    ",q$, lib_info4$, q$,", #92"
 writeln 1,"                    ",q$, lib_info5$, q$
 writeln 1,"EndMacro"
 writeln 1,""
 writeln 1," ! load the spectra"
 writeln 1,""
 i=1
 while i<=nentries
  writeln 1,"Name Entry_",i:0:0
  mathfunc trunc,i/3,value
  dad read,i
  conv mess1$,"converting entry ",i:0:0," from ",nentries:0:0," ",COMP_name$
  mess mess1$,,0,-2
  draw 3,x
  gets head,x,1
  npnts=npoints
  write   1," MakeNewSpecObj ",xlow:0:1,",",(xhigh-xlow)/(npnts-1):0:1
  writeln 1,",",npnts:0:0,",",i:0:0,",",ret_time:0:3,", #92 "
  writeln 1,"                ",q$,comp_name$,q$,", #92 "
  writeln 1,"                ",q$,comp_info$,q$
  j=1
  mess "Writing data to file"
  write 1," NewData "
  while j<=npnts
   gets index,1,j-1,x,1
   write 1,value:0:3,","
   mathfunc trunc,j/10,value
   if j-10*value=0
    writeln 1,""
    write 1," NewData "
   endif
   j=j+1
  endwhile
  writeln 1,""
  writeln 1," AddTheConvEntry ",ID_Num:0:0,",",q$,Comp_ID$,q$
  writeln 1,"EndMacro"
  writeln 1,""
  clear x
  i=i+1
 endwhile
 writeln 1,""
 writeln 1,"StartLibConversion"
 writeln 1,"Remove StartLibConversion"
 writeln 1,""
 writeln 1,"! Read the spectra"
 i = 1
 while i<=nentries
  writeln 1,"Entry_",i:0:0
  writeln 1,"Remove Entry_",i:0:0
  i=i+1
 endwhile
 writeln 1,""
 writeln 1,"! Save the library"
 writeln 1,"CloseNewConvLibrary"
 writeln 1,""
 Fclose 1
 Return
 
