import numpy as np

k1 = np.arange(24).reshape(4,6)
print(k1*5)
k2 = np.arange(45).reshape(9,5)
print(k2)
print("\n")
print(np.hsplit(k1,2))

a = np.array([20,70,90,20,40,55,66])

a[a > 50] = 40
print(a)

b = np.array([])

def sigmoid(k1):
    return 1/(1 + np.exp(-(k1)))

print(sigmoid(k1))

actual = np.random.randint(1,50,16).reshape(4,4)
predicted = np.random.randint(1,50,24).reshape(4,6)

print(actual @ predicted)

import matplotlib.pyplot as plt

x = np.linspace(-10,10,100) 
y = x
print("\n")
print(plt.plot(x,y))
plt.show()

x = np.linspace(2,2,100)
y = np.linspace(-1,1,100)
xv,yv= np.meshgrid(x,y)
f = np.exp(- xv**2-yv**2)

plt.figure(figsize=(6, 3))
plt.pcolormesh(xv,yv,f,shading='auto')
plt.colorbar()
plt.grid()
plt.show()

import pandas as pd 
l = [10,20,30,40]

print(pd.Series(l,index = ['a','b','c','d']))

