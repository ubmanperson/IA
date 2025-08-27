'use client'
import Head from 'next/head';
import Chat from '../../components/Chat';

export default function Home() {
  return (
    <>
      <Head>
        <title>CSV Chatbot</title>
      </Head>
      <main className="main-container flex justify-center items-center ">
        <Chat />
      </main>
    </>
  );
}
