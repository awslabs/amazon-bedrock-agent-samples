#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { GrafanaStack } from '../lib/grafana-stack';
import { SyntheticTelemetryApplicationStack } from '../lib/synthetic-telemetry-application-stack';

const app = new cdk.App();
new GrafanaStack(app, 'AmazonManagedGrafanaStack');
new SyntheticTelemetryApplicationStack(app, 'SyntheticTelemetryApplicationStack');
