      * Real AcuCOBOL STOCK file shape (indexed/DYNAMIC access, full CRUD verb
      * set) — the same fixture shape proven by Phase 05's
      * test_extract_cobol_data.py (TestIndexedDynamicAccessFullVerbSet). Added
      * to this repo so extract_cobol_data.py also produces non-empty CRUD
      * output here, alongside inline_screen.cbl's SCREEN SECTION output.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. STOCKPROG.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT NOT OPTIONAL
                  STOCK   ASSIGN DISK
                          LOCK MANUAL
                          WITH LOCK ON MULTIPLE RECORDS
                          STATUS WS-STATUS
                          ACCESS DYNAMIC
                          ORGANIZATION INDEXED
                          RECORD STK-CODE
                          ALTERNATE RECORD STK-ACODE DUPLICATES
                          ALTERNATE RECORD STK-BSEQ = STK-BIN STK-CODE
                          ALTERNATE RECORD STK-DKEY DUPLICATES.
       DATA DIVISION.
       FILE SECTION.
       FD  STOCK     IS EXTERNAL
           LABEL RECORD STANDARD
           VALUE OF FILE-ID W02-STOCKF.
       01  STK-RECORD1.
           03  STK-CODE.
               05  STK-ITEM     PIC X(14).
               05  STK-PLU REDEFINES STK-ITEM PIC 9(14).
           03  STK-ACODE   PIC X(10).
           03  STK-QUANT   PIC S9(09)V9(04) COMP-3.
       PROCEDURE DIVISION.
       OPEN-STOCK.
           OPEN I-O STOCK.

       READ-STOCK.
           READ STOCK  WITH IGNORE LOCK
               KEY IS STK-CODE.
         IF WS-STATUS = "00"
             MOVE ZERO   TO WS-F-ERROR
             GO TO READ-STOCK-EXIT.
         IF WS-STATUS = "23"
             MOVE 22     TO WS-F-ERROR
             GO TO READ-STOCK-EXIT.
       READ-STOCK-EXIT.
           EXIT.

       START-AT-STOCK-CODE.
           START STOCK
               KEY >= STK-CODE.
           GO TO STOCK-CHECK-STATUS.

       STOCK-CHECK-STATUS.
           EXIT.

       REWRITE-STOCK.
           REWRITE STK-RECORD1.
         IF WS-STAT1 NOT = "0"
             MOVE 22     TO WS-F-ERROR
             PERFORM WRITE-ERROR.
           GO TO WRITE-STOCK-EXIT.

       DELETE-STOCK-REC.
           DELETE STOCK.
         IF WS-STAT1 NOT = "0"
             MOVE 22     TO WS-F-ERROR
             PERFORM WRITE-ERROR.
           UNLOCK STOCK.
           GO TO WRITE-STOCK-EXIT.

       WRITE-STOCK.
           WRITE STK-RECORD1.
         IF WS-STAT1 NOT = "0"
             MOVE 22     TO WS-F-ERROR
             PERFORM WRITE-ERROR.
       WRITE-STOCK-EXIT.
           EXIT.

       WRITE-ERROR.
           EXIT.
