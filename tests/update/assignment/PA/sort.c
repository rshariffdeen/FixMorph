#include <stdio.h>
#include <string.h>

struct Book {
  char title[50];
  int book_id;
  int rank;
} book;

void selectionSort(struct Book list[], int n) {
  int j, i, min, pos, book_id, rank;
  struct Book temp;
  i = 0;

  while (i < n) {
    book_id = list[i].book_id;
    rank = list[i].rank;
    min = rank;
    pos = i;
    for (j = i + 1; j < n; j++) {
      if (list[j].rank < min) {
        min = list[j].rank;
        pos = j;
      }
    }

    temp = list[i];
    list[i] = list[pos];
    list[pos] = temp;
    i++;
  }

}

int main(void) {
  struct Book books[5];

  /* book 1 specification */
  strcpy(books[0].title, "C Programming");
  books[0].book_id = 695407;
  books[0].rank = 200;

  /* book 2 specification */
  strcpy(books[1].title, "Telecom Billing");
  books[1].book_id = 645700;
  books[1].rank = 12;

  /* book 3 specification */
  strcpy(books[2].title, "Harry Potter");
  books[2].book_id = 6463407;
  books[2].rank = 3;

  /* book 4 specification */
  strcpy(books[3].title, "Lord of the Rings");
  books[3].book_id = 6635700;
  books[3].rank = 9;

  /* book 5 specification */
  strcpy(books[4].title, "Fundamentals of Thermo Dynamics");
  books[4].book_id = 6375407;
  books[4].rank = 35;

  selectionSort(books, 5);

  for (int i = 0; i < 5; i++)
    printf("%s\n", books[i].title);

  return 0;
}
