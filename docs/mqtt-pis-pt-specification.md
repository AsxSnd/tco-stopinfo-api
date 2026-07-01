<h1>MQTT-PIS-PT V1.6.0</h1>

# Topics

|  | Retain | QoS | Interval [s] |
| --- | --- | --- | --- |
| &nbsp; |  |  |  |
| V1.0 |  |  |  |
| [pis/0/sensors/stop\_button](#Topics/Stop-Button.md) | Retain | 1 |  |
| [pis/0/sensors/door](#Topics/Door-Status.md) | Retain | 1 |  |
| [pis/0/journey](#Topics/Journey.md) | Retain | 1 |  |
| [pis/0/destination](#Topics/Destination.md) | Retain | 1 |  |
| [pis/0/linkprogress](#Topics/Link-Progress.md) |  | 0 | 1 |
| [pis/0/stopinfo](#Topics/Stop-Info.md) | Retain | 1 |  |
| [pis/0/list/stops](#Topics/Stop-List.md) | Retain | 1 |  |
| [pis/0/connections](#Topics/Connections.md) | Retain | 1 |  |
| [pis/0/journeystate](#Topics/Journey-State.md) | Retain | 1 |  |
| &nbsp; |  |  |  |
| V1.1 |  |  |  |
| [pis/0/passenger\_info\_state](#Topics/Passenger-Info-State.md) | Retain | 1 |  |
| [pis/0/vehicle/exit\_sides](#Topics/Exit-Side.md) | Retain | 1 |  |
| &nbsp; |  |  |  |
| V1.2 |  |  |  |
| [pis/0/destination/override](#Topics/Destination-Override.md) | Retain | 1 |  |
| [pis/0/vehicle/gnss\_location](#Topics/GNSS-Location.md) |  | 1 | 1 |
| [pis/0/vehicle\_formation](#Topics/Vehicle-Formation.md) | Retain | 1 |  |
| [pis/0/toilet\_status](#Topics/Toilet-Status.md) | Retain | 1 |  |
| [pis/0/door\_locking\_status](#Topics/Door-Locking-Status.md) | Retain | 1 |  |
| [pis/0/alarm\_activation](#Topics/Alarm-Activation.md) | Retain | 1 |  |
| [pis/0/passenger\_load](#Topics/Passenger-Load.md) | Retain | 1 |  |
| [pis/0/passenger\_count](#Topics/Passenger-Count.md) | Retain | 1 |  |
| [pis/0/announcement](#Topics/Announcement.md) | Retain | 1 |  |
| [pis/0/list/announcements](#Topics/Announcement-Queue.md) | Retain | 1 |  |
| [pis/0/list/announcements/status](#Topics/Announcement-Queue-Status.md) | Retain | 1 |  |
| [pis/0/line\_service\_status](#Topics/Line-Service-Status.md) | Retain | 1 |  |
| [pis/0/list/destinations](#Topics/Destination-List.md) | Retain | 1 |  |
| &nbsp; |  |  |  |
| V1.4 |  |  |  |
| [pis/0/shape](#Topics/Shape.md) | Retain | 1 |  |
| &nbsp; |  |  |  |
| V1.5 |  |  |  |
| [pis/0/journey\_sign\_on](#Topics/Journey-Sign-On.md) | Retain | 1 |  |
| [pis/0/journey\_sign\_on\_result](#Topics/Journey-Sign-On-Result.md) | Retain | 1 |  |
| [pis/0/list/stop\_waypoints](#Topics/Waypoint-List.md) | Retain | 1 |  |

<a id="Topics/Stop-Button.md" name="Topics/Stop-Button.md"></a>
## Stop Button

Indicates whether a passenger has pressed the stop button. Topic is sensors/ because of backward compatibility, it is not limited to sensors.

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/sensors/stop\_button |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | no |

### Content Schema

This topic indicates the state of the digital input from the stop button.

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| stopPressed | required |  Boolean |  |  | Indicates if any passenger has pressed the stop button |


<a id="Topics/Door-Status.md" name="Topics/Door-Status.md"></a>
## Door Status

Indicates the state of the doors. Topic is sensors/ because of backward compatibility, it is not limited to sensors.

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/sensors/door |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | no |

### Content Schema

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| doorOpen | required |  Boolean |  |  | Indicates if any door is open\. It is false if all door locks are activated |
| perDoor | optional |  Array |  | [] |  |
| &nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;doorName | optional |  String |  |  | Unique identifier of the door |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;doorOpen | optional |  Boolean |  |  | Indicates if the door is open |


<a id="Topics/Journey.md" name="Topics/Journey.md"></a>
## Journey

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/journey |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | no |

### Content Schema

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| lineNumber | required |  String, Null |  |  | Keyed in by the driver or selected from pis/0/list/journeys\. Note that this is the technical line number\. This value is null if no journey is active\. |
| journeyNumber | required |  String, Null |  |  | Keyed in by the driver or selected from pis/0/list/journeys\. This value is null if no journey is active\. |
| vehicleJourneyRef | optional |  String |  |  | The assembled vehicle journey reference\. |
| showDestination | optional |  Boolean |  |  | If true, the ‘Not in traffic’ phase is skipped and the destination is shown\. |
| errors | optional |  Array |  |  | HTTP error code when downloading\. Normally empty\. |
| &nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;message | required |  String |  |  |  |
| next | optional |  Array |  |  | The first journey in the current block that has not yet been selected\. Initially it is the journey that is closest in time\. If no block is active or no journey is left to select, this field is a null set\. |
| &nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;lineNumber | optional |  String |  |  | Keyed in by the driver or selected from pis/0/list/journeys\. Note that this is the technical line number\. This value is null if no journey is active\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;journeyNumber | optional |  String |  |  | Keyed in by the driver or selected from pis/0/list/journeys\. This value is null if no journey is active\. |


<a id="Topics/Destination.md" name="Topics/Destination.md"></a>
## Destination

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/destination |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | no |

### Content Schema

shows the current destination. This is basically what is currently shown on the front sign of the vehicle. The subtopic pis/0/destination/change (retain: false) can be used by another party to set the current destination. Only the number shall be included in this case unless the line number is unbound for the destination and a journey is not in process, in which case the lineNumber field has to be specified as well.

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| number | optional |  Integer |  |  | This number is used by the driver to identify the destination and to convert it to the destination name |
| notInTraffic | optional |  Boolean |  |  | Indicates if the destination sign shows ‘Not in traffic’ |
| name | optional |  String |  |  | The current destination name prefixed by the public line number |
| finalDestinationName | optional |  String |  |  | The name of the final stop |
| externalDisplay | optional |  Object |  |  | The name is irrelevant\. The information in here is not only for external displays\. |
| &nbsp;&nbsp;&nbsp;&nbsp;lineNumber | optional |  String |  |  | The public line number to be shown to the passengers |
| &nbsp;&nbsp;&nbsp;&nbsp;destinationName | optional |  String |  |  | The current destination name |
| &nbsp;&nbsp;&nbsp;&nbsp;destinationName_Multilanguage | optional |  Object |  |  | The current destination name |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{name} | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;viaDestinationName | optional |  String |  |  | Additional destination name |
| &nbsp;&nbsp;&nbsp;&nbsp;viaDestinationName_Multilanguage | optional |  Object |  |  | The current destination name |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{name} | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;lineCode | optional |  Integer |  |  | A more technical line code\. There is no reason it is an integer\. If alphanumeric line codes are required another property has to be added\. |


<a id="Topics/Link-Progress.md" name="Topics/Link-Progress.md"></a>
## Link Progress

This topic indicates the vehicle's current position in relation to the next stop. It can also contain estimated arrival times for following stops and the destination.

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/linkprogress |
| Retain | no |
| Quality of Service | 0 |
| Publish Interval [s] | 1 |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | no |

### Content Schema

Indicates the vehicle's current position in relation to the next stop or current stop (while it is standing at a stop). It can also contain estimated arrival times for following stops and the destination.

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| callSequenceNumber | required |  Integer |  |  | The index of the next stop in pis/0/list/stops plus 1\. This number is incremented when the stop is left\. |
| distance | optional |  Integer |  |  | The distance to next stop in meters\. It is zero while the vehicle is within the stop's radius\. |
| expectedArrivalTime | optional |  String |  |  |  |
| delaySeconds | optional |  Integer |  |  | The delay of the arrival time at the current or next stop in seconds |
| expectedDepartureTime | optional |  String |  |  |  |
| departureDelaySeconds | optional |  Integer |  |  | The delay of the departure from the current or next stop in seconds |
| expectedArrivalTimeDestination | optional |  String |  |  | The last known estimate of arrival time at the destination in seconds\. |
| followingStops | optional |  Array |  |  | Contains information about stops following the next stop\. |
| &nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;callSequenceNumber | required |  Integer |  |  | The index of the stop in pis/0/list/stops plus 1\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;expectedArrivalTime | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;delaySeconds | optional |  Integer |  |  | The delay of the arrival time at the stop in seconds |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;expectedDepartureTime | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;departureDelaySeconds | optional |  Integer |  |  | The delay of the departure from the stop in seconds |


<a id="Topics/Stop-Info.md" name="Topics/Stop-Info.md"></a>
## Stop Info

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/stopinfo |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | no |

### Content Schema

Shows the current stop within the current route and optionally the estimated arrival time for the next stop and the destination. All fields are optional because an empty json object means there is no previous or current stop.

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| callSequenceNumber | optional |  Integer |  |  | The index of the previous or current stop \(if the vehicle is standing at a stop\) in pis/0/list/stops \+ 1 \. |
| type | optional |  String | , ARRIVAL, DEPARTURE, PASSAGE |  |  |
| vehicleJourneyRef | optional |  String |  |  | A unique identifier of the journey |
| estimate | optional |  Object |  |  | Obsolete |
| &nbsp;&nbsp;&nbsp;&nbsp;callSequenceNumberNext | required |  Integer |  |  | Index of next timed stop in in pis/0/list/stops \+ 1\. i\.e\. the stop that has the estimated time stated in estimatedTimeOfArrivalNext\. It may be callSequenceNumber \+ 1, but it may also be a timing point further down the route\. |
| &nbsp;&nbsp;&nbsp;&nbsp;delay | optional |  Integer |  |  | The number of seconds the vehicle is behind the schedule\. A negative value indicates that the vehicle is before schedule\. |


<a id="Topics/Stop-List.md" name="Topics/Stop-List.md"></a>
## Stop List

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/list/stops |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | no |

### Content Schema

Contains the stops for the selected journey. They are implicitly numbered from one and upwards. Note that there is a possibility to use blind stops. These have attribute “blind”: true and shall not be shown. A stop can also be marked as cancelled. In this case it should be displayed in an obvious way to the passengers that the vehicle will not stop.

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| vehicleJourneyRef | optional |  String |  |  | A unique identifier of the journey |
| stops | required |  Array |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;number | required |  Integer |  |  | The call sequence number of the stop |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;pointRef | optional |  String |  |  | A unique identifier of the stop |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;name | required |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;name_Multilanguage | optional |  Object |  |  | The stop name in different languages |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{name} | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;zone | optional |  Integer |  |  | Ticket zone number |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;zoneCode | optional |  String |  |  | Ticket zone code\. Alphanumeric version of 'zone'\. Publishers should provide both 'zone' and 'zoneCode' if possible\. Subscribers should consider both but prioritize 'zoneCode' over 'zone'\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;distanceFromPrevious | optional |  Integer |  |  | Distance in metres following the route links |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;minutesFromPrevious | optional |  Integer |  |  | Approximate time between stops |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;estimatedArrivalFull | optional |  String |  |  | Planned time of arrival |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;estimatedDepartureFull | optional |  String |  |  | Planned time of departure |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;location | optional |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;latitude | required |  Number | \>= \-90, \<= 90 |  | An angle in degrees where 90° is at the north pole, 0° at the equator and \-90° at the south pole\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;longitude | required |  Number | \>= \-180, \<= 180 |  | An angle in degrees from \-180° to 180°\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;tolerance | optional |  Number |  |  | Size of the stop zone in metres |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;blind | optional |  Boolean |  |  | true if the stop should be invisible to passengers\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;cancelled | optional |  Boolean |  |  | true if the stop has been inhibited\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;isTimingPoint | optional |  Boolean |  |  | true if the stop is a timing point which means the vehicle must not depart before the estimated departure time has passed\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;designation | optional |  String |  |  | The label of the stop point where the bus will stop, e\.g\. A |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;alightingAllowed | optional |  Boolean |  | true | false if alighting is not allowed\. Assume allowed if property is not present\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;boardingAllowed | optional |  Boolean |  | true | false if boarding is not allowed\. Assume allowed if property is not present |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;stopCode | optional |  String |  |  | Stop code used for real time information |


<a id="Topics/Connections.md" name="Topics/Connections.md"></a>
## Connections

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/connections |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | no |

### Content Schema

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| callSequenceNumber | optional |  Integer |  |  | The stop index where the connections are valid |
| expiryDateTime | required |  String |  |  | Do not present this information after this time\. ISO 8601, UTC |
| heading | optional |  String |  |  | Optional\. The heading to be displayed\. |
| heading_Multilanguage | optional |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;{name} | optional |  String |  |  |  |
| displayDurationSeconds | optional |  Integer |  |  | Optional\. The recommended number of seconds the transfer options shall be presented\. This value depends on the number of items and content type, reflecting the time it takes for a passenger to read it\. |
| message | optional |  String |  |  | Optional\. Text to be presented when no transfer option information is available for a stop where transfer options usually are presented\. Example 1: “No departures from City Centre within the next 20 minutes”\. Example 2: “Due to technical problems, departures cannot be displayed at the moment\.” |
| message_Multilanguage | optional |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;{name} | optional |  String |  |  |  |
| situationMessages | optional |  Array |  |  | A list of situation messages that are currently relevant to the passengers onboard the vehicle at this point in the vehicle journey\. |
| &nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;heading | required |  String |  |  | The heading to be displayed\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;heading_Multilanguage | optional |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{name} | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;body | required |  String |  |  | Message body |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;body_Multilanguage | optional |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{name} | optional |  String |  |  |  |
| connections | required |  Array |  | [] | A list of connections at the upcoming stop\. |
| &nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;transportModeCode | optional |  String |  |  | The transport mode\. “BUS”, “TRAM”, “FERRY” etc\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;lineAuthorityCode | optional |  String |  |  | Short abbreviation for the organisation providing the connecting journey\. “SJ”, “ÖTåg”, “SL” etc\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;lineDesignation | required |  String |  |  | The public line number displayed to passengers for the connecting journey\. Observe that this value can be alphanumeric\! |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;directionName | optional |  String |  |  | Optional\. Name of direction for connecting journey\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;directionName_Multilanguage | optional |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{name} | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;stopAreaName | optional |  String |  |  | Optional\. Name of stop for the connecting journey\. Only included if different stop than the stop this vehicle stops at\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;stopAreaName_Multilanguage | optional |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{name} | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;stopPointDesignation | optional |  String |  |  | Optional\. Platform/track/gate number or letter as shown to the public for the stop of the connecting journey\. This is for local orientation within a stop area, bus terminal or station\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;minChangeDurationSeconds | optional |  Integer |  |  | The minimum number of seconds needed to transfer \(walk\) between the involved vehicles\. May need to be multiplied by some factors depending on different passenger abilities\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;maxWaitingUntilTime | optional |  String |  |  | Optional\. The date and time when the connection guarantee ends\. The fetcher vehicle may leave at this time even if feeder vehicle has not yet arrived\. ISO 8601, UTC\. This time is valid for the next journey of this line only\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;departures | optional |  Array |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;plannedDepartureTime | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;expectedDepartureTime | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;departureDelaySeconds | optional |  Integer |  |  | Delay of the departure in seconds |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;cancelled | optional |  Boolean |  |  | Indicates the connections is cancelled |


<a id="Topics/Journey-State.md" name="Topics/Journey-State.md"></a>
## Journey State

This topic indicates the current state of the journey. It is to be used by a GUI to show suitable info and to give the driver possibility to select e.g. to activate the journey.

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/journeystate |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | no |

### Content Schema

This message indicates the current state of the journey. It is to be used by a GUI to show suitable info and to give the driver possibility to select e.g. to activate the journey.

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| atDateTime | required |  String |  |  | Current time at publication |
| departureDateTime | optional |  String |  |  | Only included if state is NOT\_IN\_TRAFFIC\_COUNTDOWN or JOURNEY\_ACTIVATED\. Can be used by GUI to show a countdown timer |
| state | required |  String | NOT\_IN\_TRAFFIC, NOT\_IN\_TRAFFIC\_COUNTDOWN, JOURNEY\_ACTIVATED, JOURNEY\_RUNNING, JOURNEY\_APPROACHING\_LAST\_STOP, JOURNEY\_ARRIVED\_AT\_DESTINATION, JOURNEY\_OFFROUTE |  |  |


<a id="Topics/Passenger-Info-State.md" name="Topics/Passenger-Info-State.md"></a>
## Passenger Info State

A project specific state that explicitly indicates what kind of information should be show to the passenger.

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/passenger\_info\_state |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | yes |

### Content Schema

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| passengerInfoState | optional |  String |  |  | A project specific state that explicitly indicates what kind of information should be show to the passenger\. |


<a id="Topics/Exit-Side.md" name="Topics/Exit-Side.md"></a>
## Exit Side

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/vehicle/exit\_sides |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | yes |

### Content Schema

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| timestamp | required |  String |  |  |  |
| exitSide | required |  String | Both, Left, Right, Unknown |  | Exit side relative to the direction of travel |


<a id="Topics/Destination-Override.md" name="Topics/Destination-Override.md"></a>
## Destination Override

Overrides all information that is published on the pis/0/destination topic and indicates that the driver has manually selected a destination.

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/destination/override |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | yes |

### Content Schema

shows the current destination. This is basically what is currently shown on the front sign of the vehicle. The subtopic pis/0/destination/change (retain: false) can be used by another party to set the current destination. Only the number shall be included in this case unless the line number is unbound for the destination and a journey is not in process, in which case the lineNumber field has to be specified as well.

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| number | optional |  Integer |  |  | This number is used by the driver to identify the destination and to convert it to the destination name |
| notInTraffic | optional |  Boolean |  |  | Indicates if the destination sign shows ‘Not in traffic’ |
| name | optional |  String |  |  | The current destination name prefixed by the public line number |
| finalDestinationName | optional |  String |  |  | The name of the final stop |
| externalDisplay | optional |  Object |  |  | The name is irrelevant\. The information in here is not only for external displays\. |
| &nbsp;&nbsp;&nbsp;&nbsp;lineNumber | optional |  String |  |  | The public line number to be shown to the passengers |
| &nbsp;&nbsp;&nbsp;&nbsp;destinationName | optional |  String |  |  | The current destination name |
| &nbsp;&nbsp;&nbsp;&nbsp;destinationName_Multilanguage | optional |  Object |  |  | The current destination name |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{name} | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;viaDestinationName | optional |  String |  |  | Additional destination name |
| &nbsp;&nbsp;&nbsp;&nbsp;viaDestinationName_Multilanguage | optional |  Object |  |  | The current destination name |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{name} | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;lineCode | optional |  Integer |  |  | A more technical line code\. There is no reason it is an integer\. If alphanumeric line codes are required another property has to be added\. |


<a id="Topics/GNSS-Location.md" name="Topics/GNSS-Location.md"></a>
## GNSS Location

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/vehicle/gnss\_location |
| Retain | no |
| Quality of Service | 1 |
| Publish Interval [s] | 1 |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | yes |

### Content Schema

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| latitude | required |  Number |  |  | Latitude as a number between \-90 and 90 in WGS84 coordinate system\. |
| longitude | required |  Number |  |  | Longitude as a number between \-180 and 180 in WGS84 coordinate system\. |
| altitude | optional |  Number |  |  | Current altitude above sea level in m\. |
| timestamp | optional |  String |  |  |  |
| speedOverGround | optional |  Number |  |  | Current speed calculated over GNSS in m/s\. |
| signalQuality | optional |  String | dGPS, Estimated, GPS, NotValid, Unknown |  | Signal quality detail\. |
| numberOfSatellites | optional |  Integer |  |  | Number of satellites used for GNSS calculation |
| horizontalDilutionOfPrecision | optional |  Number |  |  | Value precision in horizontal direction |
| verticalDilutionOfPrecision | optional |  Number |  |  | Value precision in vertical direction |
| trackDegreeTrue | optional |  Number |  |  | Course information relative to the true North Pole in decimal degree |
| trackDegreeMagnetic | optional |  Number |  |  | Course information relative to the magnetic North Pole in decimal degree |
| gnssType | optional |  String | GPS, Glonass, Galileo, Beidou, IRNSS, Other, DeadReckoning, MixedGNSSTypes |  | Used GNSS\-System |
| gnssCoordinateSystem | optional |  String | WGS84 | "WGS84" | Information about the reference system of coordinates\. Currently always WGS84\. |


<a id="Topics/Vehicle-Formation.md" name="Topics/Vehicle-Formation.md"></a>
## Vehicle Formation

Describes the units and cars within a vehicle and how they are ordered relative to the direction of travel. Also describes where the devices within a vehicle are located.

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/vehicle\_formation |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | yes |

### Content Schema

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| units | required |  Array |  |  | Units within the vehicle formation ordered ascending relative to the direction of travel \(first unit at the front, last unit at the rear\)\. |
| &nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;unitNumber | required |  String |  |  | A unique identifier of the unit within the vehicle formation\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;cars | optional |  Array |  | [] | Cars within the unit ordered ascending relative to the direction of travel\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;carNumber | required |  String |  |  | A unique identifier of the car within the vehicle formation\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;carName | optional |  String |  |  | Only for diagnostics\. Unique within the unit\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;carLetter | required |  String |  |  | The car letter used by the passenger or personal to identify the car within the vehicle formation\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;devices | optional |  Array |  | [] | Devices within the car\. The order is not relevant\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;deviceType | required |  String |  |  | Only for diagnostics\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ipAddress | required |  String |  |  | Used to identify the device within the vehicle formation\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;hostname | optional |  String |  |  | Only for diagnostics\. |
#### Example

```json
{
  "units": [
    {
      "unitNumber": "200471",
      "cars": [
        {
          "carNumber": "39212",
          "carName": "DPT1",
          "carLetter": "A",
          "devices": [
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.0.2"
            },
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.0.3"
            }
          ]
        },
        {
          "carNumber": "39745",
          "carName": "MS1",
          "carLetter": "B",
          "devices": [
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.0.4"
            },
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.0.5"
            }
          ]
        },
        {
          "carNumber": "39565",
          "carName": "MS2",
          "carLetter": "C",
          "devices": [
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.0.6"
            },
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.0.7"
            }
          ]
        },
        {
          "carNumber": "39859",
          "carName": "MS3",
          "carLetter": "D",
          "devices": [
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.0.8"
            },
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.0.9"
            }
          ]
        },
        {
          "carNumber": "39857",
          "carName": "MS4",
          "carLetter": "E",
          "devices": [
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.0.10"
            },
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.0.11"
            }
          ]
        },
        {
          "carNumber": "39129",
          "carName": "DPT2",
          "carLetter": "F",
          "devices": [
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.0.12"
            },
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.0.13"
            }
          ]
        }
      ]
    },
    {
      "unitNumber": "200522",
      "cars": [
        {
          "carNumber": "39702",
          "carName": "DPT1",
          "carLetter": "G",
          "devices": [
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.1.14"
            },
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.1.15"
            }
          ]
        },
        {
          "carNumber": "39313",
          "carName": "MS1",
          "carLetter": "H",
          "devices": [
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.1.16"
            },
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.1.17"
            }
          ]
        },
        {
          "carNumber": "39264",
          "carName": "MS2",
          "carLetter": "I",
          "devices": [
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.1.18"
            },
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.1.19"
            }
          ]
        },
        {
          "carNumber": "39761",
          "carName": "MS3",
          "carLetter": "J",
          "devices": [
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.1.20"
            },
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.1.21"
            }
          ]
        },
        {
          "carNumber": "39238",
          "carName": "MS4",
          "carLetter": "K",
          "devices": [
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.1.22"
            },
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.1.23"
            }
          ]
        },
        {
          "carNumber": "39916",
          "carName": "DPT2",
          "carLetter": "L",
          "devices": [
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.1.24"
            },
            {
              "deviceType": "TFT",
              "ipAddress": "192.168.1.25"
            }
          ]
        }
      ]
    }
  ]
}
```


<a id="Topics/Toilet-Status.md" name="Topics/Toilet-Status.md"></a>
## Toilet Status

Describes the status (in service / out of service, not occupied / unoccupied) of all toilets within the vehicle.

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/toilet\_status |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | yes |

### Content Schema

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| toilets | optional |  Array |  | [] | All toilets within the vehicle\. If cars are specified, the toilets within the cars do not need to be repeated here\. |
| &nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;toiletName | required |  String |  |  | A unique identifier of the toilet within its scope \(vehicle or car\)\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;toiletType | required |  String | Unisex, Male, Female, PRM\-Accessible, PRM\-Only |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;toiletStatus | required |  String | InService, OutOfService |  |  |
| cars | optional |  Array |  | [] | All cars within the vehicle\. |
| &nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;carNumber | required |  String |  |  | A unique identifier of the car within the vehicle\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;toilets | optional |  Array |  | [] | All toilets within the car\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;toiletName | required |  String |  |  | A unique identifier of the toilet within its scope \(vehicle or car\)\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;toiletType | required |  String | Unisex, Male, Female, PRM\-Accessible, PRM\-Only |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;toiletStatus | required |  String | InService, OutOfService |  |  |
#### Example

```json
{
  "cars": [
    {
      "carNumber": "39212",
      "toilets": [
        {
          "toiletName": "Toilet 1",
          "toiletType": "PRM-Accessible",
          "toiletStatus": "InService"
        }
      ]
    },
    {
      "carNumber": "39129",
      "toilets": [
        {
          "toiletName": "Toilet 1",
          "toiletType": "Unisex",
          "toiletStatus": "InService"
        }
      ]
    },
    {
      "carNumber": "39702",
      "toilets": [
        {
          "toiletName": "Toilet 1",
          "toiletType": "Unisex",
          "toiletStatus": "OutOfService"
        }
      ]
    },
    {
      "carNumber": "39916",
      "toilets": [
        {
          "toiletName": "Toilet 1",
          "toiletType": "PRM-Accessible",
          "toiletStatus": "InService"
        }
      ]
    }
  ]
}
```


<a id="Topics/Door-Locking-Status.md" name="Topics/Door-Locking-Status.md"></a>
## Door Locking Status

Describes the status (locked/unlocked, not open/closed) at the current/next stop of all doors within the vehicle.

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/door\_locking\_status |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | yes |

### Content Schema

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| doors | optional |  Array |  | [] | Cars within the vehicle\. |
| &nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;carNumber | required |  String |  |  | A unique identifier of the car within the vehicle\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;doorStatus | optional |  String | Unknown, Unlocked, Locked |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;doorStatusDescription | optional |  String |  |  | A description of the status\. |
#### Example

```json
{
  "cars": [
    {
      "carNumber": "39212",
      "doorStatus": "Locked",
      "doorStatusDescription": "Doors locked by SDO (cannot open)"
    },
    {
      "carNumber": "39745",
      "doorStatus": "Locked",
      "doorStatusDescription": "Doors locked by SDO (cannot open)"
    },
    {
      "carNumber": "39565",
      "doorStatus": "Unlocked",
      "doorStatusDescription": "Doors available (can open)"
    },
    {
      "carNumber": "39859",
      "doorStatus": "Unlocked",
      "doorStatusDescription": "Doors available (can open)"
    },
    {
      "carNumber": "39857",
      "doorStatus": "Unlocked",
      "doorStatusDescription": "Doors available (can open)"
    },
    {
      "carNumber": "39129",
      "doorStatus": "Unlocked",
      "doorStatusDescription": "Doors available (can open)"
    },
    {
      "carNumber": "39702",
      "doorStatus": "Unlocked",
      "doorStatusDescription": "Doors available (can open)"
    },
    {
      "carNumber": "39313",
      "doorStatus": "Unlocked",
      "doorStatusDescription": "Doors available (can open)"
    },
    {
      "carNumber": "39264",
      "doorStatus": "Unlocked",
      "doorStatusDescription": "Doors available (can open)"
    },
    {
      "carNumber": "39761",
      "doorStatus": "Unlocked",
      "doorStatusDescription": "Doors available (can open)"
    },
    {
      "carNumber": "39238",
      "doorStatus": "Locked",
      "doorStatusDescription": "Doors locked by SDO (cannot open)"
    },
    {
      "carNumber": "39916",
      "doorStatus": "Locked",
      "doorStatusDescription": "Doors locked by SDO (cannot open)"
    }
  ]
}
```


<a id="Topics/Alarm-Activation.md" name="Topics/Alarm-Activation.md"></a>
## Alarm Activation

Reports the activation of alarms to be displayed to the vehicle personal.

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/alarm\_activation |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | yes |

### Content Schema

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| type | required |  String |  |  | A unique identifier of the alarm type\. This value is project specific and has no meaning outside of a project\. |
| text | required |  String |  |  | The text to be displayed to the personal\. |
| description | optional |  String |  |  | A description of the alarm\. Only for diagnostics\. |
#### Example

```json
{
  "type": "PAU",
  "text": "C8 D",
  "description": "PAU activated for Car 1 Door D"
}
```


<a id="Topics/Passenger-Load.md" name="Topics/Passenger-Load.md"></a>
## Passenger Load

Reports the amount of passenger on board in relation to the passenger capacity.

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/passenger\_load |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | yes |

### Content Schema

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| timestamp | required |  String |  |  |  |
| journey | required |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;vehicleNumber | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;vehicleJourneyRef | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;routeNumber | optional |  String |  |  |  |
| cars | optional |  Array |  | [] |  |
| &nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;carNumber | required |  String |  |  | A unique identifier of the car within the vehicle formation\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;occupancyPercentage | optional |  Number |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;countQuality | optional |  String | NotCounting, Good, Bad |  |  |
#### Example

```json
{
  "timestamp": "2020-09-07T06:10:00Z",
  "journey": {
    "vehicleNumber": "7217",
    "vehicleJourneyRef": "G36467",
    "routeNumber": "G"
  },
  "cars": [
    {
      "carNumber": "39212",
      "occupancyPercentage": 32,
      "countQuality": "Good"
    },
    {
      "carNumber": "39745",
      "countQuality": "NotCounting"
    },
    {
      "carNumber": "39565",
      "occupancyPercentage": 90,
      "countQuality": "Good"
    },
    {
      "carNumber": "39859",
      "occupancyPercentage": 33,
      "countQuality": "Good"
    },
    {
      "carNumber": "39857",
      "occupancyPercentage": 32,
      "countQuality": "Good"
    },
    {
      "carNumber": "39129",
      "occupancyPercentage": 29,
      "countQuality": "Good"
    },
    {
      "carNumber": "39702",
      "occupancyPercentage": 20,
      "countQuality": "Good"
    },
    {
      "carNumber": "39313",
      "occupancyPercentage": 40,
      "countQuality": "Good"
    },
    {
      "carNumber": "39264",
      "occupancyPercentage": 45,
      "countQuality": "Good"
    },
    {
      "carNumber": "39761",
      "occupancyPercentage": 36,
      "countQuality": "Good"
    },
    {
      "carNumber": "39238",
      "occupancyPercentage": 32,
      "countQuality": "Good"
    },
    {
      "carNumber": "39916",
      "occupancyPercentage": 30,
      "countQuality": "Good"
    }
  ]
}
```


<a id="Topics/Passenger-Count.md" name="Topics/Passenger-Count.md"></a>
## Passenger Count

Reports the amount of passenger on board, boarded and alighted at the previous stop.

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/passenger\_count |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | yes |

### Content Schema

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| timestamp | required |  String |  |  |  |
| journey | required |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;vehicleNumber | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;vehicleJourneyRef | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;routeNumber | optional |  String |  |  |  |
| stop | required |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;stopName | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;pointRef | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;position | optional |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;latitude | required |  Number | \>= \-90, \<= 90 |  | An angle in degrees where 90° is at the north pole, 0° at the equator and \-90° at the south pole\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;longitude | required |  Number | \>= \-180, \<= 180 |  | An angle in degrees from \-180° to 180°\. |
| alightingCount | optional |  Integer |  |  |  |
| boardingCount | optional |  Integer |  |  |  |
| onboardCount | optional |  Integer |  |  | Number of passenger currently on board\. |
| countQuality | optional |  String | NotCounting, Good, Bad | "Good" |  |
| cars | optional |  Array |  | [] |  |
| &nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;carNumber | required |  String |  |  | A unique identifier of the car within the vehicle formation\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;alightingCount | optional |  Integer |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;boardingCount | optional |  Integer |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;onboardCount | optional |  Integer |  |  | Number of passenger currently on board\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;doors | optional |  Array |  | [] |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;doorName | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;alightingCount | optional |  Integer |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;boardingCount | optional |  Integer |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;countQuality | optional |  String | NotCounting, Good, Bad |  |  |
#### Example

```json
{
  "timestamp": "2020-09-07T06:10:00Z",
  "journey": {
    "vehicleNumber": "7217",
    "vehicleJourneyRef": "G36467",
    "routeNumber": "G"
  },
  "stop": {
    "stopName": "London central station",
    "pointRef": "9025001000061245",
    "position": {
      "latitude": 59.851356,
      "longitude": 11.581231
    }
  },
  "alightingCount": 8,
  "boardingCount": 18,
  "onboardCount": 42,
  "countQuality": "Good",
  "cars": [
    {
      "carNumber": "9032444",
      "alightingCount": 8,
      "boardingCount": 18,
      "onboardCount": 32,
      "doors": [
        {
          "doorName": "Door A",
          "alightingCount": 6,
          "boardingCount": 10,
          "countQuality": "Good"
        },
        {
          "doorName": "Door B",
          "alightingCount": 2,
          "boardingCount": 8,
          "countQuality": "Bad"
        }
      ]
    },
    {
      "carNumber": "9059345",
      "alightingCount": 6,
      "boardingCount": 1,
      "onboardCount": 10,
      "doors": [
        {
          "doorName": "Door A",
          "alightingCount": 6,
          "boardingCount": 10,
          "countQuality": "Good"
        },
        {
          "doorName": "Door B",
          "countQuality": "NotCounting"
        }
      ]
    }
  ]
}
```


<a id="Topics/Announcement.md" name="Topics/Announcement.md"></a>
## Announcement

A message to be displayed to the passengers.

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/announcement |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | yes |

### Content Schema

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| messageId | optional |  String |  |  | A unique identifier of the message for logging and proof of play feedback\. |
| messageType | optional |  String | Adhoc, Predefined |  | Type of the message\. Can be used to show messages with different layouts\. |
| message | optional |  Array |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;language | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;heading | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;body | optional |  String |  |  |  |
#### Example

```json
{
  "messageId": "00000004",
  "messageType": "Adhoc",
  "message": [
    {
      "language": "en",
      "body": "Marry Christmas"
    },
    {
      "language": "de",
      "body": "Frohe Weihnachten"
    }
  ]
}
```


<a id="Topics/Announcement-Queue.md" name="Topics/Announcement-Queue.md"></a>
## Announcement Queue

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/list/announcements |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | yes |

### Content Schema

Contains at least all messages that are to be played now or in the future. Messages that were already reported back with a status other than 'Queued' do not need to be listed. Messages not listed but already queued and not yet played by the recipient will be viewed as cancelled and will be removed from the recipients queue. The recipient will report back the status of at least the messages listed here.

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| messages | optional |  Array |  | [] |  |
| &nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;messageId | required |  String |  |  | Unique identifier for the message\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;predefinedMessageId | optional |  String |  |  | Identifier for predefined messages in the static database\. If not specified, property 'text' is used\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;message | optional |  Array |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;language | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;heading | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;body | optional |  String |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;start | optional |  String |  |  | Start of the message validity period |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;end | optional |  String |  |  | End of the message validity period |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;position | optional |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;latitude | required |  Number | \>= \-90, \<= 90 |  | An angle in degrees where 90° is at the north pole, 0° at the equator and \-90° at the south pole\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;longitude | required |  Number | \>= \-180, \<= 180 |  | An angle in degrees from \-180° to 180°\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;radius | optional |  Number | \>=0 | 250 | Radius of the GPS zone \(in meters\) |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;direction | optional |  String |  |  | Project specific direction the vehicle must have so the message is played\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;repetitions | optional |  Integer | \>=1 | 1 | Number of times the message should be repeated\. |
#### Example

```json
{
  "messages": [
    {
      "messageId": "00000001",
      "predefinedMessageId": "0040",
      "start": "2024-12-04T11:10:00Z",
      "end": "2024-12-04T11:15:00Z"
    },
    {
      "messageId": "00000002",
      "predefinedMessageId": "1020",
      "start": "2024-12-04T11:40:00Z",
      "end": "2024-12-04T11:45:00Z",
      "direction": "Up"
    },
    {
      "messageId": "00000004",
      "start": "2024-12-24T12:00:00Z",
      "end": "2024-12-24T13:00:00Z",
      "message": [
        {
          "language": "en",
          "body": "Marry Christmas"
        },
        {
          "language": "de",
          "body": "Frohe Weihnachten"
        }
      ]
    },
    {
      "messageId": "00000005",
      "predefinedMessageId": "0300",
      "start": "2024-12-04T11:40:00Z",
      "end": "2024-12-04T11:45:00Z",
      "direction": "Down"
    }
  ]
}
```


<a id="Topics/Announcement-Queue-Status.md" name="Topics/Announcement-Queue-Status.md"></a>
## Announcement Queue Status

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/list/announcements/status |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | yes |

### Content Schema

Contains tha statuses of at least all messages listed in list/passenger_messages. If not all messages are included, it means list/passenger_messages was not yet received or processed.

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| messages | optional |  Array |  | [] |  |
| &nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;messageId | required |  String |  |  | Unique identifier for the message\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;status | required |  String | Queued, Played, Outdated, Rejected, Cancelled |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;playCount | optional |  Integer |  |  | Only optionally provided of status is 'Played' |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;rejectedReason | optional |  String |  |  | An optional text provided if status is 'Rejected' describing why it was rejected\. |
#### Example

```json
{
  "messages": [
    {
      "messageId": "00000001",
      "status": "Outdated"
    },
    {
      "messageId": "00000002",
      "status": "Rejected",
      "rejectedReason": "Destination did not match"
    },
    {
      "messageId": "00000003",
      "status": "Cancelled"
    },
    {
      "messageId": "00000004",
      "status": "Queued"
    },
    {
      "messageId": "00000005",
      "status": "Played",
      "playCount": 3
    }
  ]
}
```


<a id="Topics/Line-Service-Status.md" name="Topics/Line-Service-Status.md"></a>
## Line Service Status

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/line\_service\_status |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | yes |

### Content Schema

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| timestamp | optional |  String |  |  |  |
| expiryTimestamp | optional |  String |  |  |  |
| lines | optional |  Array |  |  | All lines to be displayed\. If not provided, it means no information is available\. |
| &nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;name | required |  String |  |  | The name of the line to be displayed to the passenger\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;code | required |  String |  |  | A unique code for the line\. Can be used for example to colorize the line text without depending on the human readable name which could change\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;transportModeCode | optional |  String |  |  | A unique project specific code for the transport mode\. Can be used for example to colorize the line text or showing an icon\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;statuses | required |  Array |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;description | required |  String |  |  | The text to be displayed to the passenger\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;severity | optional |  Integer |  | 0 | The severity of the status\. A higher number means a higher severity\. Can be used for example to order and colorize the status texts\. |
#### Example

```json
{
  "lines": [
    {
      "name": "Bakerloo",
      "code": "BAKRERLOO",
      "transportModeCode": "TUBE",
      "statuses": [
        {
          "description": "Good Service"
        },
        {
          "description": "Elevator Defect",
          "severity": 1
        }
      ]
    },
    {
      "name": "Metropolitan",
      "code": "METROPOLITAN",
      "transportModeCode": "TUBE",
      "statuses": [
        {
          "description": "Severe Delays",
          "severity": 9
        }
      ]
    }
  ]
}
```


<a id="Topics/Destination-List.md" name="Topics/Destination-List.md"></a>
## Destination List

This topic contains a list of destinations.

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/list/destinations |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | no |

### Content Schema

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| destinations | required |  Array |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;number | optional |  Integer |  |  | The destination number |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;name | optional |  String |  |  | The destination name |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;lineNumber | optional |  String |  |  | The destination line number |


<a id="Topics/Shape.md" name="Topics/Shape.md"></a>
## Shape

This topic contains a single shape.

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/shape |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | no |

### Content Schema

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| id | optional |  String |  |  | The unique Id of the shape if it exists\. |
| points | required |  Array |  |  | The shape's location points ordered from departure to arrival\. |
| &nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;latitude | required |  Number | \>= \-90, \<= 90 |  | An angle in degrees where 90° is at the north pole, 0° at the equator and \-90° at the south pole\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;longitude | required |  Number | \>= \-180, \<= 180 |  | An angle in degrees from \-180° to 180°\. |
#### Example

```json
{
  "id": "165483",
  "points": [
    {
      "latitude": 39.26542,
      "longitude": -76.58354
    },
    {
      "latitude": 39.26628,
      "longitude": -76.586
    }
  ]
}
```


<a id="Topics/Journey-Sign-On.md" name="Topics/Journey-Sign-On.md"></a>
## Journey Sign On

Sign on to a journey from the vehicle to a remote service providing passenger information.

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/journey\_sign\_on |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | yes |

### Content Schema

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| vehicleJourneyRef | required |  String |  |  |  |


<a id="Topics/Journey-Sign-On-Result.md" name="Topics/Journey-Sign-On-Result.md"></a>
## Journey Sign On Result

Result of the sign on to a journey. Indicates whether sign on was successful.

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/journey\_sign\_on\_result |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | yes |

### Content Schema

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| vehicleJourneyRef | required |  String |  |  |  |
| success | required |  Boolean |  |  | A value indicating whether signing on to the journey was successful |
| errorMessage | optional |  String |  |  | An error message describing what went wrong while signing on to the journey\. Should only be included if 'success' is false\. |


<a id="Topics/Waypoint-List.md" name="Topics/Waypoint-List.md"></a>
## Waypoint List

This topic contains a list of stop waypoints.

| <!-- --> | <!-- --> |
| --- | --- |
| Topic | pis/0/list/stop\_waypoints |
| Retain | yes |
| Quality of Service | 1 |
| Publish Interval [s] |  |
| Content Type | JSON |
| Content Encoding | UTF-8 |
| Zero Byte Content Allowed | no |

### Content Schema

Contains a list of stop point detection data.

| Property | Required | Type | Range | Default | Description |
| --- | --- | --- | --- | --- | --- |
| vehicleJourneyRef | optional |  String |  |  | A unique identifier of the journey |
| waypoints | required |  Array |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;[0..] |  |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;pointRef | required |  String |  |  | A unique identifier of the associated stop\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;sequenceNumber | optional |  Integer | \>=1 |  | An indicator for the order of the waypoints in a journey\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;location | optional |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;latitude | required |  Number | \>= \-90, \<= 90 |  | An angle in degrees where 90° is at the north pole, 0° at the equator and \-90° at the south pole\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;longitude | required |  Number | \>= \-180, \<= 180 |  | An angle in degrees from \-180° to 180°\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;detection | optional |  Object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;enteringDistance | optional |  Number |  |  | Entering distance in m\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;exitingDistance | optional |  Number |  |  | Exiting distance in m\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;enteringDirection | optional |  Number | \>= 0, \<= 360 |  | Entering direction in decimal degrees relative to the true north pole\. The opposite value \(\+180°\) will be used as exiting direction\. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;maxEnteringDirectionDeviation | optional |  Number | \>= 0, \<= 180 |  | Max deviation in decimal degrees\. The tolerance will be applied in both directions from the entering direction \(clockwise and counter clockwise\), effectively doubling it\. If not specified, a project specific default will be used\. |
#### Example

```json
{
  "vehicleJourneyRef": "70000264",
  "waypoints": [
    {
      "pointRef": "90002029",
      "sequenceNumber": 2,
      "location": {
        "latitude": 49.00923,
        "longitude": 8.40446
      },
      "detection": {
        "enteringDistance": 15
      }
    },
    {
      "pointRef": "90002031",
      "sequenceNumber": 2,
      "location": {
        "latitude": 49.00937,
        "longitude": 8.40444
      },
      "detection": {
        "enteringDistance": 15,
        "exitingDistance": 10,
        "passingDirection": 91,
        "maxPassingDirectionDeviation": 3
      }
    },
    {
      "pointRef": "90002032",
      "sequenceNumber": 3,
      "location": {
        "latitude": 49.00938,
        "longitude": 8.40443
      },
      "detection": {
        "passingDirection": 271,
        "maxPassingDirectionDeviation": 3
      }
    }
  ]
}
```


# Changelog

## 1.0

Initial version. Took over topics from other repositories and cleanup.

- added topics
  - stop button (stop requested)
  - door status (open/closed)
  - journey
  - journey state
  - destination
  - link progress
  - stop info
  - stop list
  - connections

## 1.1

- added topics
  - passenger info state
  - exit side

## 1.2

- added topics
  - gnss location
  - destination override
  - vehicle formation
  - toilet status
  - door locking status
  - alarm activation
  - passenger load
  - passenger count
  - announcements (queue, status, announcement)
  - line service status


## 1.3

- added property zoneCode to pis/0/list/stops.stops to allow alphanumeric zones

## 1.4

- added shape topic

## 1.5

- added journey sign on topic
- added waypoint topic

## 1.6

- added detection to stop waypoints
