"use client";
import "@h5web/app/dist/styles.css";
import { App, H5GroveProvider } from "@h5web/app";
import { useEffect, useState } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { Stack, CircularProgress } from '@mui/material';
import Image from "next/image";

const Fallback = () => (
  <div
    style={{
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      flexDirection: "column",
      height: "100vh",
    }}
  >
    <Image src={"/monkey.webp"} alt={"Monkey holding excellent website award"} />
    <h1>Something Went Wrong</h1>
    <p>
      Return <a href={"https://reduce.isis.cclrc.ac.uk"}>Home</a>
    </p>
    <p>
      If this keeps happening email{" "}
      <a href={"mailto:fia@stfc.ac.uk"}>fia-support</a>.
    </p>
  </div>
);

export default function NexusViewer(props: {
  filename: string;
  instrument: string;
  experimentNumber: string;
  apiUrl: string;
}) {
  // We need to turn the env var into a full url as the h5provider can not take just the route.
  // Typically, we expect API_URL env var to be /plottingapi in staging and production
  const [filepath, setFilePath] = useState<string>("");
  const [token, setToken] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [groveApiUrl, setApiUrl] = useState<string>(props.apiUrl)

  useEffect (() => {
    setLoading(true)
    const loadedToken = localStorage.getItem("scigateway:token") ?? ""
    setToken(loadedToken);
    setApiUrl(props.apiUrl.includes("localhost") ? props.apiUrl : `${window.location.protocol}//${window.location.hostname}/plottingapi`)

    const fileQueryUrl = `${props.apiUrl}/find_file/instrument/${props.instrument}/experiment_number/${props.experimentNumber}`
    const fileQueryParams = `filename=${props.filename}`;
    const headers: { [key: string]: string } = {'Content-Type': 'application/json'};
    console.log("Token set as: " + loadedToken)
    if (loadedToken != "") {
      headers['Authorization'] = `Bearer ${loadedToken}`;
    }

    fetch(`${fileQueryUrl}?${fileQueryParams}`, {method: 'GET', headers})
      .then((res) => {
          if (!res.ok) {
            throw new Error(res.statusText);
          }
          return res.text();
      })
      .then((data) => {
          const filepath_to_use = data.split("%20").join(" ").replace(/"/g, "")
          setFilePath(filepath_to_use);
          setLoading(false)
      })
    }, [props.apiUrl, props.instrument, props.experimentNumber, props.filename])

  return (
    <ErrorBoundary FallbackComponent={Fallback}>
      { loading ? (
        <Stack spacing={2} sx={{justifyContent: 'center', alignItems: 'center', height: '100%', width: '100%'}}>
         <p>Finding your file</p>
         <CircularProgress/>
        </Stack>
      ) : (
      <H5GroveProvider
        url={groveApiUrl}
        filepath={filepath}
        axiosConfig={{
          params: { file: filepath },
          headers: {
            Authorization: `Bearer ${token}`,
          }
        }}
      >
        <App propagateErrors />
      </H5GroveProvider> )}
    </ErrorBoundary>
  );
}
