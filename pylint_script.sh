for file in $(find . -name "*.py")
do
  echo "Checking $file"
  pylint $file
done
