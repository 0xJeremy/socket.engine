#include <iostream>
#include <string>
#include <vector>

using namespace std;

#ifndef CONNECTION_H
#define CONNECTION_H

class connection {
public:
	connection(string name);
	void receive();
	void connect(string name, string addr, int port);
	string get(string channel);
	void write(string channel, string data);
	void close();


private:
	void __start();
	void __run();
	void __cascade();
	void __close();

	string name;
	string addr;
	int port;
	bool canWrite;
	int timeout;
	int size;
	bool stopped;
	bool opened;

};

#endif
