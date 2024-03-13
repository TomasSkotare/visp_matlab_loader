function [doubleVal, stringVal, cellVal, structVal, logicalVal] = getnextfivetypes(inputVal)
    % Convert the integer to double
    doubleVal = double(inputVal) +0.5;
    
    % Convert the integer to string
    stringVal = num2str(inputVal);
    
    % Store the integer in a cell array
    cellVal = {inputVal};
    
    % Store the integer in a struct
    structVal = struct('Value', inputVal);
    
    % Convert the integer to a logical value (0 if inputVal is 0, 1 otherwise)
    logicalVal = logical(inputVal);
end