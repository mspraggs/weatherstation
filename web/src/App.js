import React, { Component } from 'react';
import './App.css';
import '../node_modules/react-vis/dist/style.css';
import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap-daterangepicker/daterangepicker.css';

import { FlexibleWidthXYPlot, LineSeries, XAxis, YAxis, Crosshair } from 'react-vis';
import { format, subHours } from "date-fns";
import { Col, Container, Row } from "react-bootstrap";

import TimeSpanPicker from "./TimeSpanPicker.js"

class App extends Component {
  constructor(props) {
    super(props);
    const toTimestamp = new Date();
    const fromTimestamp = subHours(toTimestamp, 12);
    this.state = {
      error: null,
      isLoaded: false,
      items: [],
      pressureCrosshairValue: false,
      temperatureCrosshairValue: false,
      humidityCrosshairValue: false,
      timestampLatest: null,
      pressureLatestValue: null,
      temperatureLatestValue: null,
      humidityLatestValue: null,
      showMenu: true,
      fromTimestamp: fromTimestamp,
      toTimestamp: toTimestamp,
    };
    this.locale = {
      "format": "d MMM yyyy @ HH:mm:ss",
      "sundayFirst": false
    };
  }

  componentDidMount() {
    this.updateTimer = setInterval(() => this.fetchLatest(), 15000);
    this.fetchLatest();
  }

  componentWillUnmount() {
    clearInterval(this.updateTimer);
  }

  setTimestamps(fromTimestamp, toTimestamp) {
    this.setState({
      fromTimestamp: fromTimestamp,
      toTimestamp: toTimestamp,
    });
    this.fetchTimeSeries(fromTimestamp, toTimestamp);
  }

  fetchTimeSeries(from, to) {
    const fromTimestamp = encodeURIComponent(from.toISOString())
    const toTimestamp = encodeURIComponent(to.toISOString())
    fetch(
      `${process.env.REACT_APP_API_URL}/readings` +
      `?from_timestamp=${fromTimestamp}` +
      `&to_timestamp=${toTimestamp}`
    ).then(res => res.json())
      .then(
        (result) => {
          this.setState({
            isLoaded: true,
            items: result,
          });
        },
        (error) => {
          this.setState({
            isLoaded: true,
            error,
          });
          console.log(error);
        },
      );
  }

  fetchLatest() {
    fetch(
      `${process.env.REACT_APP_API_URL}/readings/latest`
    ).then(res => res.json()).then(
      (result) => {
        this.setState({
          timestampLatest: new Date(result.timestamp),
          pressureLatestValue: result.sea_level_air_pressure,
          temperatureLatestValue: result.temperature,
          humidityLatestValue: result.relative_humidity,
        })
      }
    )
  }

  extractTimeSeries(items, dataExtractor) {
    return items.map(
      (item) => {
        return {
          x: new Date(item.timestamp),
          y: dataExtractor(item),
        }
      }
    )
  }

  render() {
    const {
      items,
      pressureCrosshairValue,
      temperatureCrosshairValue,
      humidityCrosshairValue,
      timestampLatest,
      pressureLatestValue,
      temperatureLatestValue,
      humidityLatestValue,
      fromTimestamp,
      toTimestamp,
    } = this.state;
    const pressureData = this.extractTimeSeries(items, (item) => item.sea_level_air_pressure);
    const temperatureData = this.extractTimeSeries(items, (item) => item.temperature);
    const humidityData = this.extractTimeSeries(items, (item) => item.relative_humidity);

    const fmt = this.locale["format"];
    const formattedLatestTimestmap =
      timestampLatest ? format(timestampLatest, fmt) : "-- --- ---- @ --:--:--";

    let getFormattedX = (v) => {
      if (v && v.x) {
        return format(v.x, fmt);
      }
      return "";
    }
    return (
      <div className="App-header">
        <Container fluid="md">
          <Row>
            <Col className="text-center">
              <h1>Týr</h1>
            </Col>
          </Row>
          <Row>
            <Col className="text-center">
              <h4>Atmospheric readings for St Albans, UK</h4>
            </Col>
          </Row>
          <Row>
            <Col md="auto">
              <p>Latest reading (on {formattedLatestTimestmap}):</p>
            </Col>
            <Col className="text-center">
              <p>{`${pressureLatestValue || "----.--"} hPa`}</p>
            </Col>
            <Col className="text-center">
              <p>{`${temperatureLatestValue || "--.-"} °C`}</p>
            </Col>
            <Col className="text-center">
              <p>{`${humidityLatestValue || "--.-"} %`}</p>
            </Col>
          </Row>
          <Row>
            <Col className="text-center">
              <h5>Graph time range</h5>
            </Col>
          </Row>
          <Row>
            <Col>
              <TimeSpanPicker
                fromTimestamp={ fromTimestamp }
                toTimestamp={ toTimestamp }
                format={fmt}
                onApply={(from, to) => this.setTimestamps(from, to)}
              />
            </Col>
          </Row>
          <Row>
            <Col className="">
              <FlexibleWidthXYPlot
                stroke="#007bff"
                xType="time"
                height={400}
                onMouseLeave={() => this.setState({ pressureCrosshairValue: false })}
              >
                <Crosshair values={pressureCrosshairValue ? [pressureCrosshairValue] : []}>
                  <div className="cross-hair">
                    <p>{getFormattedX(pressureCrosshairValue)}</p>
                    <p>{pressureCrosshairValue.y}</p>
                  </div>
                </Crosshair>
                <XAxis />
                <YAxis title="Pressure / hPa" />
                <LineSeries
                  data={pressureData}
                  onNearestX={(d) => this.setState({ pressureCrosshairValue: d })}
                />
              </FlexibleWidthXYPlot>
            </Col>
          </Row>
          <Row>
            <Col>
              <FlexibleWidthXYPlot
                stroke="#007bff"
                xType="time"
                height={400}
                onMouseLeave={() => this.setState({ temperatureCrosshairValue: false })}
              >
                <Crosshair values={temperatureCrosshairValue ? [temperatureCrosshairValue] : []}>
                  <div className="cross-hair">
                    <p>{getFormattedX(temperatureCrosshairValue)}</p>
                    <p>{temperatureCrosshairValue.y}</p>
                  </div>
                </Crosshair>
                <XAxis />
                <YAxis title="Temperature / °C" />
                <LineSeries
                  data={temperatureData}
                  onNearestX={(d) => this.setState({ temperatureCrosshairValue: d })}
                />
              </FlexibleWidthXYPlot>
            </Col>
          </Row>
          <Row>
            <Col>
              <FlexibleWidthXYPlot
                stroke="#007bff"
                xType="time"
                height={400}
                onMouseLeave={() => this.setState({ humidityCrosshairValue: false })}
              >
                <Crosshair values={humidityCrosshairValue ? [humidityCrosshairValue] : []}>
                  <div className="cross-hair">
                    <p>{getFormattedX(humidityCrosshairValue)}</p>
                    <p>{humidityCrosshairValue.y}</p>
                  </div>
                </Crosshair>
                <XAxis />
                <YAxis title="Relative Humidity / %" />
                <LineSeries
                  data={humidityData}
                  onNearestX={(d) => this.setState({ humidityCrosshairValue: d })}
                />
              </FlexibleWidthXYPlot>
            </Col>
          </Row>
        </Container>
      </div >
    );
  }
}

export default App;
