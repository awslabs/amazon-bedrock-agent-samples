import React from "react";
import './App.css';
import { Authenticator, View, Text, useTheme, Heading, ThemeProvider } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import LayoutApp from "./components/LayoutApp";
import { Amplify } from 'aws-amplify';
import '@aws-amplify/ui-react/styles.css';
import config from './amplifyconfiguration.json';
import { APP_NAME } from './env';

Amplify.configure(config);

function App({ signOut, user }) {

  const components = {
    Header() {
      const { tokens } = useTheme();
      return (
        <View textAlign="center" padding={tokens.space.large}>
          <Heading level={2} color="var(--amplify-colors-brand-primary-60)" fontWeight={tokens.fontWeights.semibold} fontSize={tokens.fontSizes.xl}>
            {APP_NAME}
          </Heading>
        </View>
      );
    },
    Footer() {
      const { tokens } = useTheme();
      return (
        <View textAlign="center" style={{ padding: '0px', margin: '0px' }}>
          <Text style={{ fontSize: '0.875rem', color: "#353740", padding: '32px 0px 16px 0px' }}> 
            &copy;{ new Date().getFullYear() }, Amazon Web Services, Inc. or its affiliates. All rights reserved.
          </Text>
          <img src="/images/Powered-By_logo-horiz_RGB.png" alt="Powered By AWS" />
        </View>
      );
    }
  };
  return (
    <ThemeProvider>
      <Authenticator
        components={components} 
      >
        <LayoutApp />
      </Authenticator>
    </ThemeProvider>
  );
}

export default App;