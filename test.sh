python pydllic.py --dll example/example.so example/example.cpp
g++ -fPIC -shared example/example.cpp -o example/example.so
export LD_LIBRARY_PATH=$(pwd)/example/:$LD_LIBRARY_PATH
python example/example.py
