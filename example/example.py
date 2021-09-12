from example_so import example


def main():
    test = example()
    for i in range(0, 5):
        ret = test.example(bytes(str(i)+" iterations", encoding="utf-8"))
        print("string: "+str(ret.a_string))
        print("float: "+str(ret.a_float))
        print("int: "+str(ret.an_int))
        print("---")
    pass


if __name__ == "__main__":
    main()
