import '../design/Pages.scss'
import React from 'react';
import axios, {
  AxiosResponse,
} from 'axios';
import { NextPageContext } from 'next'
import Layout from '../layout/Layout'

const title = 'Fares data build tool';
const description = 'Fares data build tool is a service that allows you to generate data in NeTEx format';

const Home = () => {
  console.log("debug");
    return (
      <Layout title={title} description={description}>
          <main className="govuk-main-wrapper app-main-class" id="main-content" role="main">
            <h1 className="govuk-heading-xl">Fares data build tool</h1>
            <p className="govuk-body-l">Use this service to:</p>
            <div className="govuk-body-l">
              <ul className="index-page-list">
                <li>Add fares to a newly registered bus service</li>
                <li>Update fares on an existing bus service</li>
                <li>Generate fares data for services in NeTEx format</li>
              </ul>
            </div>

            <a href="/operator" role="button" draggable="false" className="govuk-button govuk-button--start" data-module="govuk-button">
              Start now
              <svg className="govuk-button__start-icon" xmlns="http://www.w3.org/2000/svg" width="17.5" height="19" viewBox="0 0 33 40" role="presentation" focusable="false">
                <path fill="currentColor" d="M0 0h13l20 20-20 20H0l20-20z" />
              </svg>
            </a>
          </main>
      </Layout>
    );
}

Home.getInitialProps = async (ctx: NextPageContext) => {
  return {};
};

export default Home;