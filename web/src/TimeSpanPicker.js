import React, { Component } from 'react';

import 'bootstrap/dist/css/bootstrap.css';
import 'react-day-picker/lib/style.css';

import { format, parse, sub } from "date-fns";
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
      showFromPicker: false,
      showToPicker: false,
    };
    this.locale = {
      "format": props.format,
    };
    this.onApply = props.onApply;
  }

  componentDidMount() {
    const { fromTimestamp, toTimestamp } = this.state;
    this.onApply(fromTimestamp, toTimestamp);
  }

  setTimestamps(fromTimestamp, toTimestamp) {
    this.setState({
      fromTimestamp: fromTimestamp,
      toTimestamp: toTimestamp,
    });
    this.onApply(fromTimestamp, toTimestamp);
  }

  setFromTimestamp(fromTimestamp) {
    const { toTimestamp } = this.state;
    this.setTimestamps(fromTimestamp, toTimestamp);
  }

  setToTimestamp(toTimestamp) {
    const { fromTimestamp } = this.state;
    this.setTimestamps(fromTimestamp, toTimestamp);
  }

  render() {
    const { fromTimestamp, toTimestamp, showFromPicker, showToPicker } = this.state;
    return (
      <Container>
        <Row className="justify-content-md-center">
          <Col className="p-0" md="auto">
            <TimePicker
              timestamp={ fromTimestamp }
              showPicker={ showFromPicker }
              format={ this.locale["format"] }
              onApply={ (t) => this.setFromTimestamp(t) }
            />
          </Col>
          <Col className="p-0" md="auto">
            <TimePicker
              timestamp={ toTimestamp }
              showPicker={ showToPicker }
              format={ this.locale["format"] }
              onApply={ (t) => this.setToTimestamp(t) }
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
    this.state = {
      timespan: null,
      autoUpdate: false,
    };
    this.onApply = props.onApply;
  }

  componentDidMount() {
    this.updateTimer = setInterval(() => this.update(), 10000);
  }

  componentWillUnmount() {
    clearInterval(this.updateTimer);
  }

  setTimespan(timespan, autoUpdate) {
    this.setState({
      timespan: timespan,
      autoUpdate: autoUpdate,
    });
    if (!timespan) {
      return;
    }
    const timestamp = sub(new Date(), timespan);
    this.onApply(timestamp);
  }

  setTimestamp(timestamp) {
    this.setState({
      autoUpdate: false,
    });
    this.onApply(timestamp);
  }

  update() {
    const { autoUpdate, timespan } = this.state;
    if (!autoUpdate || !timespan) {
      return;
    }
    this.onApply(sub(new Date(), timespan));
  }

  renderPicker() {
    const { autoUpdate, timespan } = this.state;
    const { timestamp } = this.props;
    return (
      <Popover className="mw-100 w-30em" transition={false}>
        <Popover.Content className="w-30em">
          <Tabs
            defaultActiveKey="relative"
            transition={false}
          >
            <Tab eventKey="relative" title="Relative">
              <RelativePicker
                autoUpdate={ autoUpdate }
                timespan={ timespan }
                onApply={ (t, u) => this.setTimespan(t, u) }
              />
            </Tab>
            <Tab eventKey="absolute" title="Absolute">
            <AbsolutePicker
              timestamp={ timestamp }
              onApply={ (t) => this.setTimestamp(t) }
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
            className="text-center mw-20em"
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
    this.state = {
      timespan: props.timespan,
      autoUpdate: props.autoUpdate,
    }
    this.onApply = props.onApply;
  }

  apply() {
    const { timespan, autoUpdate } = this.state;
    this.onApply(timespan, autoUpdate);
  }

  render() {
    const { timespan, autoUpdate } = this.state;
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
              onChange={(e) => this.setState({
                timespan: makeNewDurationWithValue(timespan, e.target.value),
              })}
              value={value || ""}
            />
          </Form.Group>
          <Form.Group as={Col}>
            <Form.Control
              custom
              id="timespan-units"
              as="select"
              onChange={(e) => this.setState({
                timespan: makeNewDurationWithUnits(timespan, e.target.value)
              })}
              value={units || "minutes"}
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
                onChange={() => {this.setState({autoUpdate: !autoUpdate})}}
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
    this.state = {
      date: new Date(props.timestamp),
      time: format(props.timestamp, "HH:mm"),
    }
  }

  handleDayClick(day) {
    this.setState({
      date: day,
    });
  }

  setTime(e) {
    this.setState({
      time: e.target.value,
    });
  }

  apply() {
    const { date, time } = this.state;
    const timestamp = parse(time, "HH:mm", date);
    this.props.onApply(timestamp);
  }

  render() {
    const { date, time } = this.state;
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