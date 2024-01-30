// Import necessary dependencies and components
import React from 'react';
import Layout from '../components/Layout';
import HowItWorks from '../components/HowItWorks';
import TimeBlock from '../components/TimeBlock';
import PredictionForm from '../components/PredictionForm';
import CommunityPrediction from '../components/CommunityPrediction';

// Define the Home page component
const Home: React.FC = () => {
  return (
    <Layout>
      <HowItWorks />
      <TimeBlock />
      <PredictionForm />
      <CommunityPrediction />
    </Layout>
  );
};

export default Home;
