int i = 0; // this should be ignored

int k(int m) {
    char i = 'a';
    char* l = "asdf";
    char newords[] = "words";
    return m - 1; /*
    this really should be ignored
    */
}

int foo(int i) {
    i -= 10;
    return i + 10 - k(-10);
}