# Copyright 2013 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
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
#

from oslo.config import cfg

from nova import db
from nova.scheduler import filters
from nova import availability_zones

CONF = cfg.CONF
CONF.import_opt('default_availability_zone', 'nova.availability_zones')


# NOTE(SlickNik): Picks hosts that are in the same AZ as the host that the
#                 instance is running on (for resizing within same AZ)
class HostAvailabilityZoneFilter(filters.BaseHostFilter):
    """Filters Hosts by availability zone of the host that an instance is on.
       This ensures that resizes only ever happen within the same AZ.

    """

    # Availabilty zones do not change within a request
    run_filter_once_per_request = True

    def host_passes(self, host_state, filter_properties):
        spec = filter_properties.get('request_spec', {})
        props = spec.get('instance_properties', {})
        host = props.get('host')

        if host:
            context = filter_properties['context'].elevated()
            az = availability_zones.get_host_availability_zone(context, host)
            metadata = db.aggregate_metadata_get_by_host(
                context, host_state.host, key='availability_zone')
            if 'availability_zone' in metadata:
                return az in metadata['availability_zone']
            else:
                return az == CONF.default_availability_zone

        return True
