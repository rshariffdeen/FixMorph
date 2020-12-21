#include <stdio.h>
#include <string.h>

struct Author {
  char name[50];
  int user_id;
  int rank;
} author;

int sort(struct Author author_list[], int length) {
  int a, b, minimum, position, author_id, rank;
  struct Author selected;
  a = 0;

  while (a < length) {
    author_id = author_list[a].user_id;
    rank = author_list[a].rank;
    min = rank;
    position = a;
    for (b = a + 1; b < length; b++) {
      if (author_list[b].rank < minimum) {
        minimum = author_list[b].rank;
        position = b;
      }
    }

    selected = author_list[a];
    author_list[a] = author_list[position];
    author_list[position] = selected;
    a++;
  }

  return 1;
}

int main(void) {
  struct Author authors[5];

  /* book 1 specification */
  strcpy(authors[0].name, "C Programming");
  authors[0].user_id = 695407;
  authors[0].rank = 200;

  /* book 2 specification */
  strcpy(authors[1].name, "Telecom Billing");
  authors[1].user_id = 645700;
  authors[1].rank = 12;

  /* book 3 specification */
  strcpy(authors[2].name, "Harry Potter");
  authors[2].user_id = 6463407;
  authors[2].rank = 3;

  /* book 4 specification */
  strcpy(authors[3].name, "Lord of the Rings");
  authors[3].user_id = 6635700;
  authors[3].rank = 9;

  /* book 5 specification */
  strcpy(authors[4].name, "Fundamentals of Thermo Dynamics");
  authors[4].user_id = 6375407;
  authors[4].rank = 35;

  sort(authors, 5);

  for (int i = 0; i < 5; i++)
    printf("%s\n", authors[i].name);

  return 0;
}
