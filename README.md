PROTOCOL:
Protocol build:
[len(CMD)][CMD][LEN(DATA)][DATA]
Protocol explanition:
1.The protocol first send 4 bytes(CONST) containing how long the command is
2.then it sends the COMMAND
3.then it sends 4 bytes(CONST) containing the length of DATA
4.and at the end it sends the DATA itself
This way, the recv knows how much to read each time/ the send knows how much to send each time, and where the data/cmd starts/end.

Client sends: CMD DATA
Server sends back: CMD <changedDATA>/"string worked/didn't work

EXAMPLE:
Client sends: SCREENSHOT  ->(no data)
Server sends back: SCREENSHOT "SCREENSHOT sent to user/failed to save screenshot/failed to send screenshot"

EXAMPLE1:
Client sends: DIR C:\Pythonfiles
Server sends back: DIR C:\Pythonfiles\2.7
                  C:\Pythonfiles\a1
                  C:\Pythonfiles\aaa.txt
                  C:\Pythonfiles\nono
EXAMPLE2:
Client sends: COPY C:\Pythonfiles\aaa.txt c:\pythonfiles\nono
Server sends back :copied file +(copies src to dst)

EXAMPLES OF SERVER:
recives-> (03 00 00 00 | 44 49 52 | 0E 00 00 00 | 43 3A 5C 70 79 74 68 6F 6E 66 69 6C 65 73)--->[3|DIR|14|C:\Pythonfiles]
sends-> ( 44 49 52 |43 3A 5C 70 79 74 68 6F 6E 66 69 6C 65 73 5C 32 2E 37 0A 43 3A 5C 70 79 74 68 6F 6E 66 69 6C 65 73 5C 61 31 0A 43 3A 5C 70 79 74 68 6F 6E 66 69 6C 65 73 5C 6E 6F 6E 6F 0A 43 3A 5C 70 79 74 68 6F 6E 66 69 6C 65 73 5C 61 61 61)--
-->[[DIR] [C:\pythonfiles\2.7\nC:\pythonfiles\a1\nC:\pythonfiles\nono\nC:\pythonfiles\aaa]]
waits with recv, till client sends, then repeats all over again

EXAMPLES OF CLIENT:
sends-> DIR C:\Pythonfiles-> (43 3A 5C 70 79 74 68 6F 6E 66 69 6C 65 73)
recives->PRINT->(( 44 49 52 |43 3A 5C 70 79 74 68 6F 6E 66 69 6C 65 73 5C 32 2E 37 0A 43 3A 5C 70 79 74 68 6F 6E 66 69 6C 65 73 5C 61 31 0A 43 3A 5C 70 79 74 68 6F 6E 66 69 6C 65 73 5C 6E 6F 6E 6F 0A 43 3A 5C 70 79 74 68 6F 6E 66 69 6C 65 73 5C 61 61 61))
-->PRINT->>>[[C:\pythonfiles\2.7\nC:\pythonfiles\a1\nC:\pythonfiles\nono\nC:\pythonfiles\aaa]]
sends server another CMD DATA.
<img width="1676" height="1075" alt="image" src="https://github.com/user-attachments/assets/60c8e237-bc4e-4106-9248-27b867aa4931" />

