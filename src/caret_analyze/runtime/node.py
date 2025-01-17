# Copyright 2021 Research Institute of Systems Planning, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

from typing import List, Optional

from .callback import CallbackBase
from .callback_group import CallbackGroup
from .node_path import NodePath
from .publisher import Publisher
from .subscription import Subscription
from .timer import Timer
from .variable_passing import VariablePassing
from ..common import Summarizable, Summary, Util
from ..exceptions import InvalidArgumentError, ItemNotFoundError
from ..value_objects import NodeStructValue


class Node(Summarizable):
    """A class that represents a node."""

    def __init__(
        self,
        node: NodeStructValue,
        publishers: List[Publisher],
        subscription: List[Subscription],
        timers: List[Timer],
        node_paths: List[NodePath],
        callback_groups: Optional[List[CallbackGroup]],
        variable_passings: Optional[List[VariablePassing]],
    ) -> None:
        """
        Construct an instance.

        Parameters
        ----------
        node : NodeStructValue
            static info
        publishers : List[Publisher]
            publishers in the node.
        subscription : List[Subscription]
            subscriptions in the node.
        timers : List[Timer]
            timers in the node.
        node_paths : List[NodePath]
            node paths in the node.
        callback_groups : Optional[List[CallbackGroup]]
            callback groups in the node.
        variable_passings : Optional[List[VariablePassing]]
            variable passings in the node.

        """
        self._val = node
        self._publishers = publishers
        self._subscriptions = subscription
        self._timers = timers
        self._paths = node_paths
        self._callback_groups = callback_groups
        self._variable_passings = variable_passings

    @property
    def callback_groups(self) -> Optional[List[CallbackGroup]]:
        """
        Get callback groups.

        Returns
        -------
        Optional[List[CallbackGroup]]
            callback groups that the node contains.

        """
        if self._callback_groups is None:
            return None
        return sorted(self._callback_groups, key=lambda x: x.callback_group_name)

    @property
    def node_name(self) -> str:
        """
        Get node name.

        Returns
        -------
        str
            node name.

        """
        return self._val.node_name

    @property
    def callbacks(self) -> Optional[List[CallbackBase]]:
        """
        Get callbacks.

        Returns
        -------
        Optional[List[CallbackBase]]
            callbacks that the node contains.

        """
        if self.callback_groups is None:
            return None
        cbs = Util.flatten([cbg.callbacks for cbg in self.callback_groups])
        return sorted(cbs, key=lambda x: x.callback_name)

    @property
    def callback_names(self) -> Optional[List[str]]:
        """
        Get callback names.

        Returns
        -------
        Optional[List[str]]
            callback names that the node contains.

        """
        if self.callbacks is None:
            return None
        return sorted(c.callback_name for c in self.callbacks)

    @property
    def variable_passings(self) -> Optional[List[VariablePassing]]:
        """
        Get variable passings.

        Returns
        -------
        Optional[List[VariablePassing]]
            Variable passings that the node contains.

        """
        return self._variable_passings

    @property
    def publishers(self) -> List[Publisher]:
        """
        Get publishers.

        Returns
        -------
        List[Publisher]
            publishers used by the node.

        """
        return sorted(self._publishers, key=lambda x: x.topic_name)

    @property
    def timers(self) -> List[Timer]:
        """
        Get timers.

        Returns
        -------
        List[Timer]
            timers that the node contains.

        """
        return sorted(self._timers, key=lambda x: x.period_ns)

    @property
    def publish_topic_names(self) -> List[str]:
        """
        Get topic names the node publishes.

        Returns
        -------
        List[str]
            topic names that the node publishes to.

        """
        return sorted(_.topic_name for _ in self._publishers)

    @property
    def paths(self) -> List[NodePath]:
        """
        Get node paths.

        Node paths are defined by subscription and publisher pair.

        Returns
        -------
        List[NodePath]
            node paths that the node contains.

        """
        return self._paths

    @property
    def subscriptions(self) -> List[Subscription]:
        """
        Get subscriptions the node subscribes.

        Returns
        -------
        List[Subscription]
            subscriptions that the node subscribes to.

        """
        return sorted(self._subscriptions, key=lambda x: x.topic_name)

    @property
    def subscribe_topic_names(self) -> List[str]:
        """
        Get subscribe topic names.

        Returns
        -------
        List[str]
            topic names to which the node subscribes.

        """
        return sorted(_.topic_name for _ in self._subscriptions)

    @property
    def callback_group_names(self) -> Optional[List[str]]:
        """
        Get callback group names.

        Returns
        -------
        Optional[List[str]]
            callback group names that the node contains.

        """
        if self.callback_groups is None:
            return None
        return sorted(_.callback_group_name for _ in self.callback_groups)

    @property
    def value(self) -> NodeStructValue:
        """
        Get StructValue object.

        Returns
        -------
        NodeStructValue
            node value.

        Notes
        -----
        This property is for CARET debugging purposes.

        """
        return self._val

    @property
    def summary(self) -> Summary:
        """
        Get summary [override].

        Returns
        -------
        Summary
            summary info.

        """
        return self._val.summary

    def get_callback_group(self, callback_group_name: str) -> CallbackGroup:
        """
        Get callback group.

        Parameters
        ----------
        callback_group_name : str
            callback group name to get.

        Returns
        -------
        CallbackGroup
            callback group that matches the condition.

        Raises
        ------
        InvalidArgumentError
            Occurs when the given argument type is invalid.
        ItemNotFoundError
            Occurs when no items were found.
        MultipleItemFoundError
            Occurs when several items were found.

        """
        if not isinstance(callback_group_name, str):
            raise InvalidArgumentError('Argument type is invalid.')

        if self._callback_groups is None:
            raise ItemNotFoundError('Callback group is None.')

        return Util.find_one(
            lambda x: x.callback_group_name == callback_group_name, self._callback_groups)

    def get_path(
        self,
        subscribe_topic_name: Optional[str],
        publish_topic_name: Optional[str],
    ) -> NodePath:
        """
        Get node path.

        Parameters
        ----------
        subscribe_topic_name : Optional[str]
            topic name to which the node subscribes.
        publish_topic_name : Optional[str]
            topic name to which the node publishes.

        Returns
        -------
        NodePath
            node path that matches the condition.

        Raises
        ------
        InvalidArgumentError
            Occurs when the given argument type is invalid.
        ItemNotFoundError
            Occurs when no items were found.
        MultipleItemFoundError
            Occurs when several items were found.

        """
        if not isinstance(subscribe_topic_name, str) and subscribe_topic_name is not None:
            raise InvalidArgumentError('Argument type is invalid.')

        if not isinstance(publish_topic_name, str) and publish_topic_name is not None:
            raise InvalidArgumentError('Argument type is invalid.')

        def is_target(path: NodePath):
            return path.publish_topic_name == publish_topic_name and \
                path.subscribe_topic_name == subscribe_topic_name

        return Util.find_one(is_target, self.paths)

    def get_callback(self, callback_name: str) -> CallbackBase:
        """
        Get callback.

        Parameters
        ----------
        callback_name : str
            callback name to get.

        Returns
        -------
        CallbackBase
            callback that matches the condition.

        Raises
        ------
        InvalidArgumentError
            Occurs when the given argument type is invalid.
        ItemNotFoundError
            Occurs when no items were found.
        MultipleItemFoundError
            Occurs when several items were found.

        """
        if not isinstance(callback_name, str):
            raise InvalidArgumentError('Argument type is invalid.')

        if self.callbacks is None:
            raise ItemNotFoundError('Callback is None.')

        return Util.find_one(lambda x: x.callback_name == callback_name, self.callbacks)

    def get_callbacks(self, *callback_names: str) -> List[CallbackBase]:
        """
        Get callbacks.

        Parameters
        ----------
        callback_names: *str
            callback names to get.

        Returns
        -------
        List[CallbackBase]
            callbacks that match the condition.

        Raises
        ------
        InvalidArgumentError
            Occurs when the given argument type is invalid.
        ItemNotFoundError
            Occurs when no items were found.

        """
        callbacks = []
        for callback_name in callback_names:
            callbacks.append(self.get_callback(callback_name))

        return callbacks

    def get_subscription(self, topic_name: str) -> Subscription:
        """
        Get subscription.

        Parameters
        ----------
        topic_name : str
            topic name to get.

        Returns
        -------
        Subscription
            Subscription instance that matches the condition.

        Raises
        ------
        InvalidArgumentError
            Occurs when the given argument type is invalid.
        ItemNotFoundError
            Occurs when no items were found.
        MultipleItemFoundError
            Occurs when several items were found.

        """
        if not isinstance(topic_name, str):
            raise InvalidArgumentError('Argument type is invalid.')

        return Util.find_one(lambda x: x.topic_name == topic_name, self._subscriptions)

    def get_publisher(self, topic_name: str) -> Publisher:
        """
        Get publisher.

        Parameters
        ----------
        topic_name : str
            publisher topic name to get.

        Returns
        -------
        Publisher
            A publisher that matches the condition.

        Raises
        ------
        InvalidArgumentError
            Occurs when the given argument type is invalid.
        ItemNotFoundError
            Occurs when no items were found.
        MultipleItemFoundError
            Occurs when several items were found.

        """
        if not isinstance(topic_name, str):
            raise InvalidArgumentError('Argument type is invalid.')

        return Util.find_one(lambda x: x.topic_name == topic_name, self._publishers)

    def get_timer(self, topic_name: str) -> Timer:
        # TODO(hsgwa): fix argument type.
        if not isinstance(topic_name, str):
            raise InvalidArgumentError('Argument type is invalid.')

        return Util.find_one(lambda x: x.topic_name == topic_name, self._timers)
