// Copyright 2021 Research Institute of Systems Planning, Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#ifndef CARET_ANALYZE_CPP_IMPL__COMMON_HPP_

#include <unordered_set>

template<
  typename T,
  typename ContainerT = std::unordered_set<T>
>
ContainerT merge_set(const ContainerT & left, const ContainerT & right)
{
  ContainerT merged;
  for (auto & elem : left) {
    merged.insert(elem);
  }
  for (auto & elem : right) {
    merged.insert(elem);
  }
  return merged;
}

#endif  // CARET_ANALYZE_CPP_IMPL__COMMON_HPP_"
#define CARET_ANALYZE_CPP_IMPL__COMMON_HPP_
