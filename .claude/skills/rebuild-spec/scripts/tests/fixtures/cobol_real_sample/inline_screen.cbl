      * Anonymized excerpt derived from a real AcuCOBOL stock-enquiry screen.
      * Author/company identifiers replaced with placeholders (see README.md).
000010 IDENTIFICATION DIVISION.
000020 PROGRAM-ID.     STKENQ01.
000030 AUTHOR.         SAMPLE-AUTHOR.
000040 DATE-WRITTEN.   JANUARY 1983.
000050 ENVIRONMENT DIVISION.
000060 CONFIGURATION SECTION.
000070 SPECIAL-NAMES.
                       CURSOR IS CSTART
                       CONSOLE IS CRT
                       CRT STATUS IS KEY-STATUS.
000080 DATA DIVISION.
000090 WORKING-STORAGE SECTION.
       77  WS-OPTION           PIC X(01).
       01  WS-ITEM-CODE        PIC X(14).
       01  WS-ITEM-DESC        PIC X(30).
      /
000100 SCREEN SECTION.

       01  MENU-SCREEN.
           03  LINE 2  COLUMN 10 VALUE "STOCK ENQUIRY MENU".
           03  LINE 4  COLUMN 10 VALUE "1. Enquire by item code".
           03  LINE 5  COLUMN 10 VALUE "2. Enquire by description".
      *    03  LINE 6  COLUMN 10 VALUE "3. (Retired) Batch export".
           03  LINE 7  COLUMN 10 VALUE "0. Exit".
           03  LINE 9  COLUMN 10 PIC X(01) USING WS-OPTION AUTO.

       01  ITEM-ENQUIRY-SCREEN.
           03  LINE 3  COLUMN 3 VALUE "Item code     ".
           03          COLUMN 20 FOREGROUND-COLOR 7 HIGHLIGHT
                                  PIC X(14) USING WS-ITEM-CODE AUTO.
           03  LINE 4  COLUMN 3 VALUE "Description   ".
           03          COLUMN 20 PIC X(30) FROM WS-ITEM-DESC.
      /
000200 PROCEDURE DIVISION.
000210 AA000-MAIN             SECTION.
000220 AA000-INIT.
              PERFORM BA000-SHOW-MENU.
              STOP RUN.

000230 BA000-SHOW-MENU        SECTION.
       BA010.
              DISPLAY MENU-SCREEN.
              ACCEPT MENU-SCREEN.
            IF WS-OPTION = "1" OR "2"
                PERFORM CA000-ITEM-ENQUIRY
            ELSE
                IF WS-OPTION NOT = "0"
                    GO TO BA010.

000240 CA000-ITEM-ENQUIRY     SECTION.
       CA010.
              DISPLAY ITEM-ENQUIRY-SCREEN.
              ACCEPT ITEM-ENQUIRY-SCREEN.
              GO TO BA010.
