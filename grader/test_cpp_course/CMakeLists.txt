project(test_cpp_course)

cmake_minimum_required(VERSION 3.5)

option(GRADER OFF "running inside grader")
option(ENABLE_PRIVATE_TESTS OFF "enable private tests")
option(TEST_SOLUTION OFF "build solution")

add_executable(test_hello hello-world/hello.cpp)
