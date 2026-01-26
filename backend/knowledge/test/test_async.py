
import  asyncio
import time


def  test():
    return 1+1

async def  test_async():
    # await 非常耗时的操作（10s）
    # 其它的业务1
    # 其它的业务2
    # 其它的业务3
    # 其它的业务4
    pass

def  test_await():
    pass
    # await 非常耗时的操作（10s）
    # 其它的业务1
    # 其它的业务2
    # 其它的业务3
    # 其它的业务4


if __name__ == '__main__':

    # print(test())
    # print(test_async())
    asyncio.run(test_async())
    # 规则：
    # 1.任意一个普通的python函数 加上async关键字字后，该方法运行完得到的是协程对象，并不是方法的返回值。
    # 2.一定要将协程对象放到拥有循环事件的环境中
    # 3.一般加了async关键字的函数，内部强烈建议使用await 关键字。await 让当前方法暂时别执行，并且让出刚刚执行这个方法的线程cpu
    # 4.只要有await 一定要让当前函数是一个能够暂停的函数。该函数前面有async关键字

    # 5.async和await一起使用。