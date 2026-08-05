      * Anonymized excerpt derived from a real AcuCOBOL screen assembled from
      * COPY'd .CRT screen segments (production convention in the source repo:
      * SCREEN SECTION rarely has inline 01 records, it COPYs them instead).
000010 IDENTIFICATION DIVISION.
000020 PROGRAM-ID.     STKHDR01.
000030 AUTHOR.         SAMPLE-AUTHOR.
000050 ENVIRONMENT DIVISION.
000060 CONFIGURATION SECTION.
000070 SPECIAL-NAMES.
                       CONSOLE IS CRT
                       CRT STATUS IS KEY-STATUS.
000080 DATA DIVISION.
000090 WORKING-STORAGE SECTION.
       01  WS-ITEM-CODE        PIC X(14).
      /
000100 SCREEN SECTION.

       COPY STOCKHDR.CRT.

       COPY LEGACYFOOTER.CRT.
      /
000200 PROCEDURE DIVISION.
000210 AA000-MAIN             SECTION.
       AA010.
              DISPLAY S-HDR.
              ACCEPT S-HDR.
              STOP RUN.
