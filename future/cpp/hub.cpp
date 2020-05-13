#include "hub.h"

using namespace std;

hub::hub(int p)
{
	port = p;
	timeout = 1;
	size = 256;
	stopped = false;
	opened = false;

}

void hub::set_timeout(int t)
{
	timeout = t;
}

void hub::set_size(int s)
{
	size = s;
}

void hub::connect(string name, string addr, int port)
{
	
}

void hub::close()
{
	stopped = true;
}
