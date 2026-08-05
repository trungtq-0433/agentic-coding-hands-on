#include <stdio.h>

void add_record(void) {
    printf("Record added.\n");
}

void delete_record(void) {
    printf("Record deleted.\n");
}

int main(void) {
    int choice;
    while (1) {
        printf("1. Add record\n");
        printf("2. Delete record\n");
        printf("3. Exit\n");
        scanf("%d", &choice);
        switch (choice) {
            case 1: add_record(); break;
            case 2: delete_record(); break;
            case 3: return 0;
        }
    }
    return 0;
}
