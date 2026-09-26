"use client";

import { useEffect, useState } from "react";
import { FiBell, FiSettings } from "react-icons/fi";
import { usePathname } from "next/navigation";

export default function Navbar() {
  const pathname = usePathname();
  const [sessionText, setSessionText] = useState("Loading shift...");

  useEffect(() => {
    setSessionText(getCurrentSession());
  }, []);

  const pageInfo: Record<
    string,
    {
      title: string;
      subtitle: string;
    }
  > = {

    "/beranda": {
      title: "ICU-Q Dashboard",
      subtitle: sessionText,
    },


    "/monitoring": {
      title: "ICU Monitoring",
      subtitle: sessionText,
    },


    "/pasien": {
      title: "ICU Patient List",
      subtitle: sessionText,
    },


    "/tambahpasien": {
      title: "ICU Patient Registration",
      subtitle: sessionText,
    },


    "/antrean": {
      title: "ICU Queue",
      subtitle: sessionText,
    },


    "/riwayat": {
      title: "Patient History",
      subtitle: sessionText,
    },


  };


  const current =
    pageInfo[pathname] ??
    {
      title: "ICU-Q",
      subtitle: sessionText,
    };


  return (
    <nav className="bg-white border-b border-gray-200 h-20 px-6 flex items-center justify-between">

      {/* Kiri */}
      <div>

        <h1 className="text-2xl font-bold text-gray-800">
          {current.title}
        </h1>


        <p className="text-sm text-gray-500">
          {current.subtitle}
        </p>

      </div>



      {/* Kanan */}
      <div className="flex items-center gap-6">


        <div className="
          flex 
          items-center 
          gap-2 
          bg-green-100 
          text-green-700 
          px-4 
          py-2 
          rounded-xl
        ">

          <FiSettings />

          <span className="font-medium">
            System Active
          </span>

        </div>



        <div className="
          flex 
          items-center 
          gap-2 
          bg-gray-100 
          px-4 
          py-2 
          rounded-xl
        ">

          <FiBell className="text-lg text-orange-500" />

          <span className="font-semibold">
            3
          </span>

        </div>


      </div>


    </nav>
  );
}



function getCurrentSession() {

  const now = new Date();


  const date = now.toLocaleDateString("en-US", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });


  const hour = now.getHours();


  let session = "Morning Shift";


  if (hour >= 12 && hour < 17) {

    session = "Afternoon Shift";

  } else if (hour >= 17) {

    session = "Night Shift";

  }


  return `${date} • ${session}`;

}