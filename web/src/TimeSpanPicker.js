import React, { Component } from 'react';

import 'bootstrap/dist/css/bootstrap.css';
import 'react-day-picker/lib/style.css';

import {
  differenceInMinutes,
  differenceInHours,
  differenceInDays,
  differenceInWeeks,
  format,
  parse,
  set,
  sub
} from "date-fns";
import DayPicker from 'react-day-picker';
import {
  Button,
  ButtonGroup,
  Col,
  Container,
  Form,
  OverlayTrigger,
  Popover,
  Row,
  Tab,
  Tabs,
  ToggleButton
} from 'react-bootstrap';


class TimeSpanPicker extends Component {
  constructor(props) {
    super(props);
    this.state = {
      fromTimestamp: props.fromTimestamp,
      toTimestamp: props.toTimestamp,
    };
    this.locale = {
      "format": props.format,
    };
    this.onApply = props.onApply;
    this.fromTimestampGenerator = () => props.fromTimestamp;
    this.toTimestampGenerator = () => props.toTimestamp;
  }

  componentDidMount() {
    const { fromTimestamp, toTimestamp } = this.state;
    this.onApply(fromTimestamp, toTimestamp);
    this.updateTimer = setInterval(() => this.update(), 30000);
  }

  componentWillUnmount() {
    clearInterval(this.updateTimer);
  }

  setTimestamps(fromTimestamp, toTimestamp) {
    if (fromTimestamp === this.state.fromTimestamp &&
      toTimestamp === this.state.toTimestamp) {
      return;
    }
    this.setState({
      fromTimestamp: fromTimestamp,
      toTimestamp: toTimestamp,
    });
    this.onApply(fromTimestamp, toTimestamp);
  }

  update() {
    const fromTimestamp = this.fromTimestampGenerator();
    const toTimestamp = this.toTimestampGenerator();
    this.setTimestamps(fromTimestamp, toTimestamp);
  }

  setFromTimestampGenerator(fromTimestampGenerator) {
    this.fromTimestampGenerator = fromTimestampGenerator;
    this.update();
  }

  setToTimestampGenerator(toTimestampGenerator) {
    this.toTimestampGenerator = toTimestampGenerator;
    this.update();
  }

  render() {
    const { fromTimestamp, toTimestamp } = this.state;
    return (
      <Container>
        <Row className="justify-content-md-center">
          <Col className="p-0" md="auto">
            <TimePicker
              timestamp={fromTimestamp}
              format={this.locale["format"]}
              onApply={(g) => this.setFromTimestampGenerator(g)}
            />
          </Col>
          <Col className="p-0" md="auto">
            <TimePicker
              timestamp={toTimestamp}
              format={this.locale["format"]}
              onApply={(g) => this.setToTimestampGenerator(g)}
            />
          </Col>
        </Row>
      </Container>
    );
  }
}

class TimePicker extends Component {
  constructor(props) {
    super(props);
    const hours = differenceInHours(new Date(), props.timestamp);
    const timespan = { hours: hours };
    this.state = {
      timespan: timespan,
      autoUpdate: false,
      timestamp: props.timestamp,
    };
    this.onApplyProp = props.onApply;
  }

  onApply(gen, extra) {
    const generator = () => {
      const timestamp = gen();
      const { units } = unpackDuration(this.state.timespan);
      const timespan = differenceInUnits(new Date(), timestamp, units);
      var autoUpdate = extra.autoUpdate;
      if (autoUpdate === null) {
        autoUpdate = this.state.autoUpdate;
      }
      this.setState({
        timestamp: timestamp,
        timespan: extra.timespan || timespan,
        autoUpdate: autoUpdate,
      });
      return timestamp;
    };
    this.onApplyProp(generator);
  }

  renderPicker() {
    const { autoUpdate, timespan, timestamp } = this.state;
    return (
      <Popover className="mw-100 w-25rem" transition={false}>
        <Popover.Content className="w-25rem">
          <Tabs defaultActiveKey="relative">
            <Tab eventKey="relative" title="Relative">
              <RelativePicker
                autoUpdate={autoUpdate}
                timespan={timespan}
                timestamp={timestamp}
                onChange={(s) => this.setState(s)}
                onApply={(g, extra) => this.onApply(g, extra)}
              />
            </Tab>
            <Tab eventKey="absolute" title="Absolute">
              <AbsolutePicker
                timestamp={timestamp}
                onChange={(s) => this.setState(s)}
                onApply={(t) => this.onApply(() => t, {})}
              />
            </Tab>
          </Tabs>
        </Popover.Content>
      </Popover>
    );
  }

  render() {
    const { timestamp } = this.props;
    return (
      <>
        <OverlayTrigger
          rootClose={true}
          trigger="click"
          placement="bottom"
          overlay={this.renderPicker()}
        >
          <Form.Control
            className="text-center mw-20rem"
            type="text"
            readonly
            value={format(timestamp, this.props.format)}
          />
        </OverlayTrigger>
      </>
    )
  }
}

class RelativePicker extends Component {
  constructor(props) {
    super(props);
    this.onChange = props.onChange;
    this.onApply = props.onApply;
  }

  apply() {
    const { autoUpdate, timespan } = this.props;
    const initialTimestamp = sub(new Date(), timespan);
    const extra = {
      timespan: timespan,
      autoUpdate: autoUpdate,
    };
    const timestampGenerator = () => {
      if (!autoUpdate) {
        return initialTimestamp;
      }
      if (!timespan) {
        return;
      }
      return sub(new Date(), timespan);
    };
    this.onApply(timestampGenerator, extra);
  }

  render() {
    const { autoUpdate, timespan } = this.props;
    const { value, units } = unpackDuration(timespan);
    return (
      <Form>
        <Form.Row className="mt-3">
          <Form.Group as={Col}>
            <Form.Control
              custom
              id="timespan-value"
              className="w-100 h-100 text-center"
              type="number"
              onChange={(e) => this.onChange({
                timespan: makeNewDurationWithValue(timespan, e.target.value),
              })}
              value={value}
            />
          </Form.Group>
          <Form.Group as={Col}>
            <Form.Control
              custom
              id="timespan-units"
              as="select"
              onChange={(e) => this.onChange({
                timespan: makeNewDurationWithUnits(timespan, e.target.value)
              })}
              value={units}
            >
              <option value="minutes">Minutes ago</option>
              <option value="hours">Hours ago</option>
              <option value="days">Days ago</option>
              <option value="weeks">Weeks ago</option>
            </Form.Control>
          </Form.Group>
        </Form.Row>
        <Form.Row>
          <Form.Group className="text-center" as={Col}>
            <ButtonGroup toggle>
              <ToggleButton
                variant="outline-secondary"
                value={1}
                type="checkbox"
                checked={autoUpdate}
                onChange={() => { this.onChange({ autoUpdate: !autoUpdate }) }}
              >Auto Update</ToggleButton>
            </ButtonGroup>
          </Form.Group>
          <Form.Group className="text-center" as={Col}>
            <Button onClick={() => this.apply()}>Apply</Button>
          </Form.Group>
        </Form.Row>
      </Form>
    )
  }
}

class AbsolutePicker extends Component {
  constructor(props) {
    super(props);
    this.onApply = this.props.onApply;
    this.onChange = this.props.onChange;
  }

  handleDayClick(day) {
    const hours = this.props.timestamp.getHours();
    const minutes = this.props.timestamp.getMinutes();
    const timestamp = set(day, { "hours": hours, "minutes": minutes });
    this.props.onChange({
      timestamp: timestamp,
    });
  }

  setTime(e) {
    const timestamp = parse(e.target.value, "HH:mm", this.props.timestamp);
    this.onChange({
      timestamp: timestamp,
    });
  }

  apply() {
    this.onApply(this.props.timestamp);
  }

  render() {
    const time = format(this.props.timestamp, "HH:mm");
    const date = this.props.timestamp;
    const selection = [date, date];
    return (
      <>
        <Container>
          <Row>
            <Col className="p-0">
              <DayPicker
                className="Selectable"
                numberOfMonths={1}
                selectedDays={selection}
                onDayClick={(d) => this.handleDayClick(d)}
              />
            </Col>
            <Col>
              <Container className="p-0">
                <Row>
                  <Col className="pl-0 pr-0 pt-3">
                    <Form.Control
                      className="text-center"
                      type="time"
                      value={time}
                      onChange={(t) => this.setTime(t)}
                    />
                  </Col>
                </Row>
                <Row>
                  <Col className="text-center pl-0 pr-0 pt-3">
                    <Button onClick={() => this.apply()}>Apply</Button>
                  </Col>
                </Row>
              </Container>
            </Col>
          </Row>
        </Container>
      </>
    )
  }
}

function unpackDuration(duration) {
  if (!duration) {
    return {
      units: null,
      value: null,
    }
  }
  const units = Object.keys(duration).pop();
  const value = duration[units];
  return {
    units: units,
    value: value,
  };
}

function differenceInUnits(lhs, rhs, units) {
  var value = null;
  if (units === "minutes") {
    value = differenceInMinutes(lhs, rhs);
  } else if (units === "hours") {
    value = differenceInHours(lhs, rhs);
  } else if (units === "days") {
    value = differenceInDays(lhs, rhs);
  } else if (units === "weeks") {
    value = differenceInWeeks(lhs, rhs);
  } else {
    throw new Error("Invalid units");
  }
  var duration = {};
  duration[units] = value;
  return duration;
}

function makeNewDurationWithUnits(duration, newUnits) {
  const { value } = unpackDuration(duration);
  let newDuration = {};
  newDuration[newUnits] = value;
  return newDuration;
}

function makeNewDurationWithValue(duration, newValue) {
  const { units } = unpackDuration(duration);
  let newDuration = {};
  newDuration[units] = newValue;
  return newDuration;
}

export default TimeSpanPicker;