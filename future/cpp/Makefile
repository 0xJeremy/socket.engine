CC = g++
CFLAGS = -Wall -Wextra -c -std=c++11
DEPS = hub.h connection.h

%.o: %.cpp $(DEPS)
	$(CC) -o $@ $< $(CFLAGS)

test: test.o hub.o connection.h
	$(CC) -o test test.o hub.o connection.h

clean:
	rm -f *.o core* *~ test