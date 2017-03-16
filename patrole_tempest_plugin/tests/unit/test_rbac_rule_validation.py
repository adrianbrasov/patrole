#    Copyright 2017 AT&T Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock
import testtools

from patrole_tempest_plugin import rbac_auth
from patrole_tempest_plugin import rbac_exceptions
from patrole_tempest_plugin import rbac_rule_validation as rbac_rv

from tempest.lib import exceptions
from tempest import test
from tempest.tests import base


class RBACRuleValidationTest(base.TestCase):

    def setUp(self):
        super(RBACRuleValidationTest, self).setUp()
        self.mock_args = mock.Mock(spec=test.BaseTestCase)
        self.mock_args.auth_provider = mock.Mock()
        self.mock_args.rbac_utils = mock.Mock()
        self.mock_args.auth_provider.credentials.tenant_id = \
            mock.sentinel.tenant_id
        self.mock_args.auth_provider.credentials.user_id = \
            mock.sentinel.user_id

    @mock.patch('patrole_tempest_plugin.rbac_auth.RbacAuthority')
    def test_RBAC_rv_happy_path(self, mock_auth):
        decorator = rbac_rv.action("", "")
        mock_function = mock.Mock()
        wrapper = decorator(mock_function)
        wrapper((self.mock_args))
        self.assertTrue(mock_function.called)

    @mock.patch('patrole_tempest_plugin.rbac_auth.RbacAuthority')
    def test_RBAC_rv_forbidden(self, mock_auth):
        decorator = rbac_rv.action("", "")
        mock_function = mock.Mock()
        mock_function.side_effect = exceptions.Forbidden
        wrapper = decorator(mock_function)

        self.assertRaises(exceptions.Forbidden, wrapper, self.mock_args)

    @mock.patch('patrole_tempest_plugin.rbac_auth.RbacAuthority')
    def test_RBAC_rv_rbac_action_failed(self, mock_auth):
        decorator = rbac_rv.action("", "")
        mock_function = mock.Mock()
        mock_function.side_effect = rbac_exceptions.RbacActionFailed

        wrapper = decorator(mock_function)
        self.assertRaises(exceptions.Forbidden, wrapper, self.mock_args)

    @mock.patch('patrole_tempest_plugin.rbac_auth.RbacAuthority')
    def test_RBAC_rv_not_allowed(self, mock_auth):
        decorator = rbac_rv.action("", "")

        mock_function = mock.Mock()
        wrapper = decorator(mock_function)

        mock_permission = mock.Mock()
        mock_permission.get_permission.return_value = False
        mock_auth.return_value = mock_permission

        self.assertRaises(rbac_exceptions.RbacOverPermission, wrapper,
                          self.mock_args)

    @mock.patch('patrole_tempest_plugin.rbac_auth.RbacAuthority')
    def test_RBAC_rv_forbidden_not_allowed(self, mock_auth):
        decorator = rbac_rv.action("", "")

        mock_function = mock.Mock()
        mock_function.side_effect = exceptions.Forbidden
        wrapper = decorator(mock_function)

        mock_permission = mock.Mock()
        mock_permission.get_permission.return_value = False
        mock_auth.return_value = mock_permission

        self.assertIsNone(wrapper(self.mock_args))

    @mock.patch('patrole_tempest_plugin.rbac_auth.RbacAuthority')
    def test_RBAC_rv_rbac_action_failed_not_allowed(self, mock_auth):
        decorator = rbac_rv.action("", "")

        mock_function = mock.Mock()
        mock_function.side_effect = rbac_exceptions.RbacActionFailed
        wrapper = decorator(mock_function)

        mock_permission = mock.Mock()
        mock_permission.get_permission.return_value = False
        mock_auth.return_value = mock_permission

        self.assertIsNone(wrapper(self.mock_args))

    @mock.patch.object(rbac_auth, 'rbac_policy_parser', autospec=True)
    def test_invalid_policy_rule_throws_skip_exception(
            self, mock_rbac_policy_parser):
        mock_rbac_policy_parser.RbacPolicyParser.return_value.allowed.\
            side_effect = rbac_exceptions.RbacParsingException

        decorator = rbac_rv.action(mock.sentinel.service,
                                   mock.sentinel.policy_rule)
        wrapper = decorator(mock.Mock())

        e = self.assertRaises(testtools.TestCase.skipException, wrapper,
                              self.mock_args)
        self.assertEqual('Attempted to test an invalid policy file or action',
                         str(e))

        mock_rbac_policy_parser.RbacPolicyParser.assert_called_once_with(
            mock.sentinel.tenant_id, mock.sentinel.user_id,
            mock.sentinel.service)
