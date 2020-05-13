#include <iostream>
#include <string>
#include <vector>
#include "connection.h"

using namespace std;

#ifndef HUB_H
#define HUB_H

class hub {
public:
	hub(int p);
	void set_timeout(int t);
	void set_size(int s);
	void connect(string name, string addr, int p);
	void close();

	vector<string> get_all(string channel);
	vector<string> get_by_name(string name, string channel);
	vector<string> get_local(string channel);
	vector<string> get_remote(string channel);

	void write_all(string channel, string data);
	void write_to_name(string name, string channel, string data);
	void write_to_local(string channel, string data);
	void write_to_remote(string channel, string data);


private:
	void __open();
	void __start();
	void __run();

	int port;
	int timeout;
	int size;
	bool stopped;
	bool opened;
	vector<connection> connections;
	vector<string> address_connections;

};

#endif
