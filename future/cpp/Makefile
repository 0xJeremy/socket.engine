CC = g++
CFLAGS = -Wall -Wextra -c -std=c++11
DEPS = hub.h connection.h socket.h

%.o: %.cpp $(DEPS)
	$(CC) -o $@ $< $(CFLAGS)

test: test.o hub.o connection.o socket.o
	$(CC) -o test test.o hub.o connection.o socket.o

clean:
	rm -f *.o core* *~ test