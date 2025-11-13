"use client";

import React from "react";

const CounterLoader = () => {
  return (
    <>
      <style jsx>{`
        .counter-loader-container {
          width: 100vw;
          height: 100vh;
          display: flex;
          justify-content: center;
          align-items: center;
          position: fixed;
          top: 0;
          left: 0;
          z-index: 9999;
          background: hsl(var(--background));
        }

        .timer {
          display: grid;
          grid-template-columns: repeat(3, 25px);
          grid-template-rows: repeat(5, 25px);
          gap: 10px;
          grid-template-areas:
            "div1 div2 div3"
            "div4 div5 div6"
            "div7 div8 div9"
            "div10 div11 div12"
            "div13 div14 div15";
        }

        .timer > div {
          background-color: hsl(var(--primary));
          border-radius: 5px;
        }

        .timer-div1 { grid-area: div1; animation: div1 10s both infinite; }
        .timer-div2 { grid-area: div2; animation: div2 10s both infinite; }
        .timer-div3 { grid-area: div3; }
        .timer-div4 { grid-area: div4; animation: div4 10s both infinite; }
        .timer-div5 { grid-area: div5; display: none; }
        .timer-div6 { grid-area: div6; animation: div6 10s both infinite; }
        .timer-div7 { grid-area: div7; animation: div7 10s both infinite; }
        .timer-div8 { grid-area: div8; animation: div8 10s both infinite; }
        .timer-div9 { grid-area: div9; }
        .timer-div10 { grid-area: div10; animation: div10 10s both infinite; }
        .timer-div11 { grid-area: div11; display: none; }
        .timer-div12 { grid-area: div12; animation: div12 10s both infinite; }
        .timer-div13 { grid-area: div13; animation: div13 10s both infinite; }
        .timer-div14 { grid-area: div14; animation: div14 10s both infinite; }
        .timer-div15 { grid-area: div15; }

        @keyframes div1 {
          0% { transform: translateX(0); }
          10% { transform: translateX(70px); }
          20% { transform: translateX(0); }
          30% { transform: translateX(0); }
          40% { transform: translateX(0); }
          50% { transform: translateX(0); }
          60% { transform: translateX(0); }
          70% { transform: translateX(0); }
          80% { transform: translateX(0); }
          90% { transform: translateX(0); }
          100% { transform: translateX(0); }
        }

        @keyframes div2 {
          0% { transform: translateX(0); }
          10% { transform: translateX(35px); }
          20% { transform: translateX(0); }
          30% { transform: translateX(0); }
          40% { transform: translateX(35px); }
          50% { transform: translateX(0); }
          60% { transform: translateX(0); }
          70% { transform: translateX(0); }
          80% { transform: translateX(0); }
          90% { transform: translateX(0); }
          100% { transform: translateX(0); }
        }

        @keyframes div4 {
          0% { transform: translateX(0); }
          10% { transform: translateX(70px); }
          20% { transform: translateX(70px); }
          30% { transform: translateX(70px); }
          40% { transform: translateX(0); }
          50% { transform: translateX(0); }
          60% { transform: translateX(0); }
          70% { transform: translateX(70px); }
          80% { transform: translateX(0); }
          90% { transform: translateX(0); }
          100% { transform: translateX(0); }
        }

        @keyframes div6 {
          0% { transform: translateX(0); }
          10% { transform: translateX(0); }
          20% { transform: translateX(0); }
          30% { transform: translateX(0); }
          40% { transform: translateX(0); }
          50% { transform: translateX(-70px); }
          60% { transform: translateX(-70px); }
          70% { transform: translateX(0); }
          80% { transform: translateX(0); }
          90% { transform: translateX(0); }
          100% { transform: translateX(0); }
        }

        @keyframes div7 {
          0% { transform: translateX(0); }
          10% { transform: translateX(70px); }
          20% { transform: translateX(0); }
          30% { transform: translateX(0); }
          40% { transform: translateX(0); }
          50% { transform: translateX(0); }
          60% { transform: translateX(0); }
          70% { transform: translateX(70px); }
          80% { transform: translateX(0); }
          90% { transform: translateX(0); }
          100% { transform: translateX(0); }
        }

        @keyframes div8 {
          0% { transform: translateX(35px); }
          10% { transform: translateX(35px); }
          20% { transform: translateX(0); }
          30% { transform: translateX(0); }
          40% { transform: translateX(0); }
          50% { transform: translateX(0); }
          60% { transform: translateX(0); }
          70% { transform: translateX(35px); }
          80% { transform: translateX(0); }
          90% { transform: translateX(0); }
          100% { transform: translateX(35px); }
        }

        @keyframes div10 {
          0% { transform: translateX(0); }
          10% { transform: translateX(70px); }
          20% { transform: translateX(0); }
          30% { transform: translateX(70px); }
          40% { transform: translateX(70px); }
          50% { transform: translateX(70px); }
          60% { transform: translateX(0); }
          70% { transform: translateX(70px); }
          80% { transform: translateX(0); }
          90% { transform: translateX(70px); }
          100% { transform: translateX(0); }
        }

        @keyframes div12 {
          0% { transform: translateX(0); }
          10% { transform: translateX(0); }
          20% { transform: translateX(-70px); }
          30% { transform: translateX(0); }
          40% { transform: translateX(0); }
          50% { transform: translateX(0); }
          60% { transform: translateX(0); }
          70% { transform: translateX(0); }
          80% { transform: translateX(0); }
          90% { transform: translateX(0); }
          100% { transform: translateX(0); }
        }

        @keyframes div13 {
          0% { transform: translateX(0); }
          10% { transform: translateX(70px); }
          20% { transform: translateX(0); }
          30% { transform: translateX(0); }
          40% { transform: translateX(70px); }
          50% { transform: translateX(0); }
          60% { transform: translateX(0); }
          70% { transform: translateX(70px); }
          80% { transform: translateX(0); }
          90% { transform: translateX(0); }
          100% { transform: translateX(0); }
        }

        @keyframes div14 {
          0% { transform: translateX(0); }
          10% { transform: translateX(35px); }
          20% { transform: translateX(0); }
          30% { transform: translateX(0); }
          40% { transform: translateX(35px); }
          50% { transform: translateX(0); }
          60% { transform: translateX(0); }
          70% { transform: translateX(35px); }
          80% { transform: translateX(0); }
          90% { transform: translateX(0); }
          100% { transform: translateX(0); }
        }
      `}</style>
      <div className="counter-loader-container">
        <div className="timer">
          <div className="timer-div1" />
          <div className="timer-div2" />
          <div className="timer-div3" />
          <div className="timer-div4" />
          <div className="timer-div5" />
          <div className="timer-div6" />
          <div className="timer-div7" />
          <div className="timer-div8" />
          <div className="timer-div9" />
          <div className="timer-div10" />
          <div className="timer-div11" />
          <div className="timer-div12" />
          <div className="timer-div13" />
          <div className="timer-div14" />
          <div className="timer-div15" />
        </div>
      </div>
    </>
  );
};

export default CounterLoader;
