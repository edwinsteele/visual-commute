create table Station (
	stationId INTEGER PRIMARY KEY,
	stationName TEXT,
	lon REAL,
	lat REAL
);

create table Trip (
	tripId INTEGER PRIMARY KEY,
	lineId INTEGER,
	timeTableType TEXT, -- WD/WE
	FOREIGN KEY(lineId) REFERENCES Line(lineId)
);
CREATE INDEX lId on Trip(lineId);

create table Line (
	lineId INTEGER,
	lineName TEXT
);

-- key should be tripId + stationId. A station can't appear more than once
--  on a particular trip (what about city circle?)
create table TripStop (
	tripStopId INTEGER PRIMARY KEY,
	tripId INTEGER,
	stationId INTEGER,
	depTime TEXT,
	FOREIGN KEY(tripId) REFERENCES Trip(tripId),
	FOREIGN KEY(stationId) REFERENCES Station(tripId)
);
CREATE INDEX tId on TripStop(tripId);
CREATE INDEX sId on TripStop(stationId);

create table Segment (
	segmentId INTEGER PRIMARY KEY,
	depTripStopId INTEGER,
	arvTripStopId INTEGER,
	FOREIGN KEY(depTripStopId) REFERENCES TripStop(tripStopId),
	FOREIGN KEY(arvTripStopId) REFERENCES TripStop(tripStopId)
);
-- A compound index may be better here...
CREATE INDEX depTS on Segment(depTripStopId);
CREATE INDEX arvTS on Segment(arvTripStopId);

create table InterchangeStation (
	lineId INTEGER,
	stationId INTEGER,
	FOREIGN KEY(lineId) REFERENCES Line(lineId),
	FOREIGN KEY(stationId) REFERENCES Station(stationId)
);



INSERT INTO LINE VALUES (1,"Blue Mountains - Lithgow to Central");
INSERT INTO LINE VALUES (2,"Blue Mountains - Central to Lithgow");
INSERT INTO LINE VALUES (3,"Western Line - Penrif to Hornsby");
INSERT INTO LINE VALUES (4,"Western Line - Hornsby to Penrif");

