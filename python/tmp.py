from socketengine import client

c = client(addr='130.64.188.10').start()
c1 = client(addr='130.64.188.10').start()

c.write('thing', 'hello there!')
c1.write('thing', 'hello there!')

