function [list1, list2, list3] = getnextthreelists(inputNumber1, inputNumber2, inputNumber3, count)
    list1 = (inputNumber1+1):inputNumber1+count;
    list2 = (inputNumber2+1):inputNumber2+count;
    list3 = (inputNumber3+1):inputNumber3+count;   
end